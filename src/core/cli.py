from __future__ import annotations

from subprocess import CalledProcessError, check_call
from dotenv import load_dotenv
from importlib.util import module_from_spec, spec_from_file_location
from inspect import Parameter, signature
from json import loads
from os import environ
from pathlib import Path
from sys import argv, modules, stderr, stdin, executable, stdout
from traceback import print_exc

from .backend import Backend
from .engine import Engine
from .report import Report
from .spec import Specification


SPEC_EXTS = {".yml", ".yaml", ".json"}


def install_requirements(project_dir: Path) -> bool:
    req = project_dir / "requirements.txt"
    if not req.is_file():
        print(f"error: missing requirements.txt in {project_dir}")
        return False

    interactive = (
        getattr(stdin, "isatty", lambda: False)()
        and getattr(stdout, "isatty", lambda: False)()
    )
    if not interactive:
        print("error: missing dependency and not in interactive mode")
        return False

    try:
        ans = input(
            f"missing dependency. Install {req.name} now? [y/N] "
        ).strip().lower()
    except KeyboardInterrupt:
        stdout.write("\n")
        stdout.flush()
        return False

    if ans not in {"y", "yes"}:
        return False

    try:
        check_call(
            [executable, "-m", "pip", "install", "-r", str(req)],
            stdout=stdout,
            stderr=stderr,
        )
        return True
    except CalledProcessError:
        print("error: pip install failed")
        return False


def banner():
    print(
        "██╗   ██╗██╗ ██████╗ ██╗██╗\n"
        "██║   ██║██║██╔════╝ ██║██║\n"
        "██║   ██║██║██║  ███╗██║██║\n"
        "╚██╗ ██╔╝██║██║   ██║██║██║\n"
        " ╚████╔╝ ██║╚██████╔╝██║███████╗\n"
        "  ╚═══╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝\n"
        "Behavioural Verification Framework\n"
        "----------------------------------\n"
        "CTRL-C to exit\n"
    )


def find_specs(project_dir: Path) -> list[Path]:
    specs: list[Path] = []
    for p in project_dir.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() not in SPEC_EXTS:
            continue
        name = p.name.lower()
        if name.endswith(".report.yml") or name.endswith(".report.yaml"):
            continue
        specs.append(p)
    return sorted(specs, key=lambda p: p.name)


def find_reports_for_spec(spec_path: Path) -> list[Path]:
    base = spec_path.stem
    reports = list(spec_path.parent.glob(f"{base}-*.report.y*ml"))
    return sorted(reports, key=lambda p: p.stat().st_mtime, reverse=True)


def load_backend(project_dir: Path) -> tuple[Backend, Path]:
    load_dotenv(project_dir / ".env")

    files = sorted(project_dir.glob("*_backend.py"))
    if not files:
        raise SystemExit(f"no *_backend.py found in {project_dir}")
    if len(files) > 1:
        raise SystemExit(
            f"multiple *_backend.py found in {project_dir}: {', '.join(p.name for p in files)}"
        )

    backend_file = files[0]

    spec = spec_from_file_location(
        f"vigil_project_backend_{abs(hash(str(backend_file)))}",
        backend_file,
    )
    if spec is None or spec.loader is None:
        raise SystemExit(f"failed to load backend module: {backend_file}")

    mod = module_from_spec(spec)
    modules[spec.name] = mod
    spec.loader.exec_module(mod)

    subclasses = [
        v for v in vars(mod).values()
        if isinstance(v, type) and issubclass(v, Backend) and v is not Backend
    ]

    if not subclasses:
        raise SystemExit(f"{backend_file.name}: no Backend subclass found")
    if len(subclasses) > 1:
        raise SystemExit(
            f"{backend_file.name}: multiple Backend subclasses found "
            f"({', '.join(c.__name__ for c in subclasses)})"
        )

    cls = subclasses[0]

    def env(key: str):
        if key not in environ:
            return None
        try:
            return loads(environ[key])
        except Exception:
            return environ[key]

    sig = signature(cls.__init__)
    kwargs: dict[str, object] = {}

    has_varkw = any(
        p.kind == Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )

    for name, p in sig.parameters.items():
        if name == "self" or p.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            continue

        val = env(name)
        if val is None:
            val = env(f"VIGIL_{name.upper()}")

        if val is None:
            if p.default is Parameter.empty:
                raise SystemExit(
                    f"{backend_file.name}: missing env for `{name}`"
                )
            continue

        kwargs[name] = val

    if has_varkw:
        for k in environ:
            if k.startswith("VIGIL_"):
                key = k[6:].lower()
                if key not in kwargs:
                    kwargs[key] = env(k)

    try:
        return cls(**kwargs), backend_file
    except TypeError as e:
        raise SystemExit(
            f"{backend_file.name}: failed to instantiate {cls.__name__}: {e}"
        )


def menu(specs: list[Path]) -> int:
    print("\nSpecs:")
    for i, p in enumerate(specs, start=1):
        print(f"  {i}. {p.name}")

        reports = find_reports_for_spec(p)[:3]
        for r in reports:
            print(f"     ↳ {r.resolve()}")
    print("")

    raw = input("> ").strip()
    try:
        idx = int(raw)
    except ValueError:
        return -1

    return idx - 1 if 1 <= idx <= len(specs) else -1


def derive_title(spec_path: Path, backend: Backend) -> str:
    stem = spec_path.stem.replace("_", " ").replace("-", " ").strip().lower()
    return f"Behavioural verification of {backend.name} with respect to {stem or 'the spec'}"


def start():
    banner()

    args = argv[1:]
    flags = {a for a in args if a.startswith("--")}
    positional = [a for a in args if not a.startswith("--")]

    if len(positional) > 1:
        raise SystemExit("usage: vigil [project_dir] [--trace]")

    project_dir = (
        Path(positional[0]).expanduser().resolve()
        if positional
        else Path.cwd().resolve()
    )

    if not project_dir.is_dir():
        raise SystemExit(f"not a directory: {project_dir}")

    backend, backend_file = load_backend(project_dir)
    engine = Engine(backend)
    report = None

    specs = find_specs(project_dir)
    if not specs:
        raise SystemExit("no spec files found")

    print(f"project: {project_dir}")
    print(f"backend: {backend.name} ({backend_file.name})")

    while True:
        try:
            choice = menu(specs)
            if choice == -1:
                continue
            spec_path = specs[choice]
            spec = Specification(str(spec_path),
                                 default_title=derive_title(spec_path, backend))
            report = Report(backend=backend,
                            inputs=spec.inputs,
                            spec_path=spec_path,
                            title=spec.title,
                            hypothesis=spec.hypothesis)

            report.print_header()
            report.section("Running variations and checks")
            engine.run(
                report=report,
                inputs=spec.inputs,
                variations=spec.variations,
                checks=spec.checks,
            )
            report.section("Writing report")
            report.write()
        except KeyboardInterrupt:
            break  # exit gracefully
        except ModuleNotFoundError as e:
            print(
                f"error: No module named '{getattr(e, 'name', None) or str(e)}'")
            if not install_requirements(project_dir):
                continue
        except Exception as e:
            if "--trace" in flags:
                print_exc()
            else:
                print(f"error: {e}")
            continue
        finally:
            if report is not None:
                report.close()
