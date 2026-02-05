from __future__ import annotations

from dotenv import load_dotenv
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
from inspect import Parameter, signature
from json import load, loads
from os import path, environ
from yaml import safe_load

from .__types__ import Input
from .check import Check
from .variation import Variation


class Specification:
    BUILTIN = {
        "variation": "builtin.variations",
        "check": "builtin.checks",
    }

    FOLDERS = {
        "variation": ["", "variations"],
        "check": ["", "checks"],
    }

    FILENAMES = {
        "variation": ["{n}.py", "{n}_variation.py"],
        "check": ["{n}.py", "{n}_check.py"],
    }

    def __init__(self, spec_path: str, default_title: str):
        self.path = spec_path
        self.folder = path.dirname(path.abspath(spec_path))

        load_dotenv(path.join(self.folder, ".env"))
        with open(spec_path, "r") as f:
            self.data = safe_load(f) if spec_path.endswith(
                (".yaml", ".yml")) else load(f)

        self.title = self.data.get("title") or default_title
        self.hypothesis = self.data.get("hypothesis")
        if not self.hypothesis:
            raise ValueError("spec must define `hypothesis`")

        self.inputs: list[Input] = []
        self._load_inputs()
        self.variations: list[Variation | None] = []
        self._load_variations()
        self.checks: list[Check] = []
        self._load_checks()

    def _load_inputs(self):
        raw = self._section("inputs")
        self.inputs: list[Input] = []

        for i, item in enumerate(raw):
            if isinstance(item, dict):
                if "data" not in item and all(k in ("id", "reference") for k in item):
                    raise ValueError(
                        "input dict must contain data or additional fields besides id/reference")
                self.inputs.append({
                    "id": str(item.get("id", i)),
                    "data": item["data"] if "data" in item else {k: v for k, v in item.items() if k not in ("id", "reference")},
                    **({"reference": item["reference"]} if "reference" in item else {}),
                })
            else:
                self.inputs.append({"id": str(i), "data": item})

    def _load_variations(self):
        raw = self._section("variations")
        self.variations = []

        def resolve(entry):
            if entry is None or entry == "none":
                return [None]

            if isinstance(entry, str):
                return [self._load("variation", {"type": entry})]

            if not isinstance(entry, dict) or "type" not in entry:
                raise ValueError(f"invalid component entry: {entry!r}")

            t = entry.get("type")

            if t == "repeat":
                times = int(entry.get("times", 1))
                if times < 0:
                    raise ValueError("repeat.times must be > 0")

                do = entry.get("do")
                if not isinstance(do, list) or not do:
                    raise ValueError("repeat.do must be a non-empty list")

                inner: list = []
                for b in do:
                    inner.extend(resolve(b))
                return inner * times

            return [self._load("variation", entry)]

        for block in raw:
            self.variations.extend(resolve(block))

        if not self.variations:
            self.variations = [None]

    def _load_checks(self):
        raw = self._section("checks")
        self.checks = []

        for block in raw:
            if isinstance(block, str):
                self.checks.append(self._load("check", {"type": block}))
            elif isinstance(block, dict) and "type" in block:
                self.checks.append(self._load("check", block))
            else:
                raise ValueError(f"invalid component entry: {block!r}")

    def _section(self, name: str):
        raw = self.data.get(name)
        if raw is None:
            raise ValueError(f"spec must define `{name}`")
        if not isinstance(raw, list):
            raw = [raw]
        if not raw:
            raise ValueError(f"spec must define at least one item in `{name}`")
        return raw

    def _env(self, key: str):
        if key not in environ:
            return None
        val = environ.get(key)
        if val is None or val == "":
            return None
        try:
            return loads(environ[key])
        except Exception:
            return environ[key]

    def _try_load_builtin(self, kind: str, name: str, cls_name: str):
        mod_name = f"{self.BUILTIN[kind]}.{name}"
        try:
            mod = import_module(mod_name)
        except ModuleNotFoundError as e:
            # Only treat it as "builtin doesn't exist" if *that* module is missing.
            if e.name == mod_name:
                return None
            raise

        if hasattr(mod, cls_name):
            return getattr(mod, cls_name)

        return None

    def _try_load_project_file(self, kind: str, name: str, cls_name: str):
        for sub in self.FOLDERS[kind]:
            for pattern in self.FILENAMES[kind]:
                candidate = path.join(self.folder, sub, pattern.format(n=name))
                if not path.exists(candidate):
                    continue

                spec = spec_from_file_location(
                    f"vigil_{kind}_{name}_{abs(hash(candidate))}", candidate
                )
                if spec is None or spec.loader is None:
                    continue

                mod = module_from_spec(spec)
                spec.loader.exec_module(mod)

                if hasattr(mod, cls_name):
                    return getattr(mod, cls_name)

        return None

    def _load(self, kind: str, block: dict) -> object:
        name = block["type"]
        cls_name = "".join(part.capitalize() for part in name.split("_"))

        cls = self._try_load_builtin(kind, name, cls_name)
        if cls is None:
            cls = self._try_load_project_file(kind, name, cls_name)

        if cls is None:
            raise ValueError(f"unable to resolve `{name}` for {kind}")

        params = {k: v for k, v in block.items() if k != "type"}
        sig = signature(cls.__init__)

        accepted = {}
        for param_name, parameter in sig.parameters.items():
            if param_name == "self" or parameter.kind == Parameter.VAR_KEYWORD:
                continue

            if param_name in params:
                accepted[param_name] = params[param_name]
                continue

            val = self._env(param_name)
            if val is not None:
                accepted[param_name] = val
                continue

            val = self._env(f"VIGIL_{param_name.upper()}")
            if val is not None:
                accepted[param_name] = val

        if any(p.kind == Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            for k, v in params.items():
                if k not in accepted:
                    accepted[k] = v

        return cls(**accepted)
