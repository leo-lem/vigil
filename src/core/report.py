from __future__ import annotations

from datetime import datetime
from enum import Enum
from itertools import cycle
from pathlib import Path
from sys import stdout
from threading import Event, Thread
from time import sleep
from typing import Any, IO
from yaml import safe_dump, SafeDumper

from .check import Check
from .variation import Variation
from .backend import Backend
from .__types__ import Input


SafeDumper.add_representer(
    str,
    lambda dumper, value: dumper.represent_scalar(
        "tag:yaml.org,2002:str",
        value,
        style="|" if "\n" in value else None,
    ),
)


class ANSI:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    CYAN = "\x1b[36m"

    @staticmethod
    def supports(stream: IO[str]) -> bool:
        return bool(getattr(stream, "isatty", lambda: False)())

    @staticmethod
    def color(enabled: bool, code: str, s: str) -> str:
        return f"{code}{s}{ANSI.RESET}" if enabled else s


class Spinner:
    def __init__(self, label: str, stream: IO[str], enabled: bool = True):
        self._label = label
        self._stream = stream
        self._enabled = bool(enabled and ANSI.supports(stream))
        self._stop = Event()
        self._thread: Thread | None = None

    def set_label(self, label: str):
        self._label = label

    def __enter__(self) -> Spinner:
        if not self._enabled:
            self._stream.write(f"{self._label}\n")
            self._stream.flush()
            return self

        if self._stop.is_set():
            self._stop = Event()

        def run() -> None:
            frames = cycle(
                ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
            while not self._stop.is_set():
                self._stream.write(f"\r{next(frames)} {self._label}")
                self._stream.flush()
                sleep(0.08)

        self._thread = Thread(target=run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.3)


class Report:
    def __init__(self, backend: Backend, inputs: list[Input], spec_path: Path, title: str, hypothesis: str):
        self._stream = stdout
        self._ansi = bool(ANSI.supports(self._stream))
        self._spinner = Spinner(
            "", self._stream, enabled=ANSI.supports(self._stream))

        self.spec_path = spec_path
        self.started = datetime.now()

        self.data: dict[str, Any] = {
            "meta": {
                "started": self.started.isoformat(timespec="seconds"),
                "spec": str(spec_path),
                "title": title,
                "hypothesis": hypothesis
            },
            "backend": {
                "type": backend.name,
                "function": dict(backend.function),
                "environment": dict(backend.environment),
            },
            "inputs": [self.sanitize(i) for i in inputs],
            "variations": [],
            "checks": [],
        }

    def print_header(self):
        self._println(f"title: {self.data['meta']['title']}")
        self._println(f"hypothesis: {self.data['meta']['hypothesis']}")
        self._println(f"backend: {self.data['backend']['type']}")
        self._println(f"spec: {self.spec_path}")
        self._println(f"time: {self.started.strftime('%Y-%m-%d %H:%M:%S')}")
        self._println("")

    def start_variation(self, index: int, total: int, variation: Variation | None):
        self._ensure_spinner()
        name = "none" if variation is None else variation.name
        self._spinner.set_label(f"variation {index + 1}/{total} · {name}")

    def finish_variation(self, index: int, total: int, variation: Variation | None, n_inputs: int, duration_s: float, extra: dict[str, Any] | None = None):
        name = "none" if variation is None else variation.name

        self.data["variations"].append(
            {
                "type": name,
                "intent": None if variation is None else self.sanitize(getattr(variation, "intent", None)),
                "n_inputs": n_inputs,
                "duration_s": duration_s,
                **(self.sanitize(extra) if extra else {}),
                **(
                    {k: self.sanitize(v) for k, v in vars(
                        variation).items() if not k.startswith("_")}
                    if variation is not None else {}
                ),
            }
        )

        self._finish_spinner_line(
            f"✔ variation {index + 1}/{total} {name} ({n_inputs} inputs, {duration_s:.2f}s)"
        )

    def start_check(self, index: int, total: int, check_name: str):
        self._ensure_spinner()
        self._spinner.set_label(f"check {index + 1}/{total} · {check_name}")

    def finish_check(self, check_name: str, severity: Check.Severity, annotation: dict[str, Any]):
        self.data["checks"].append(
            {
                "type": check_name,
                "result": {
                    "severity": severity.label,
                    **self.sanitize(annotation),
                },
            }
        )

        msg = f"{severity.icon} {check_name} ({severity.label})"
        color = self._severity_color(severity)
        self._finish_spinner_line(ANSI.color(self._ansi, color, msg))

    def write(self) -> Path:
        out_path = self.spec_path.with_name(
            f"{self.spec_path.stem}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.report.yml"
        )

        with out_path.open("w", encoding="utf-8") as f:
            safe_dump(self.sanitize(self.data), f,
                      allow_unicode=True, sort_keys=False)

        self._println(f"wrote report to {out_path}.")
        self.close()
        return out_path

    def close(self) -> None:
        if self._spinner._thread is not None:
            self._spinner.__exit__(None, None, None)

    def section(self, title: str) -> None:
        self._println(f"\n▶ {title}", ANSI.BOLD)

    def ok(self, msg: str) -> None:
        self._println(f"✔ {msg}", ANSI.GREEN + ANSI.BOLD)

    def warn(self, msg: str) -> None:
        self._println(f"⚠ {msg}", ANSI.YELLOW + ANSI.BOLD)

    def fail(self, msg: str) -> None:
        self._println(f"✖ {msg}", ANSI.RED + ANSI.BOLD)

    def _ensure_spinner(self) -> None:
        if self._spinner._thread is None:
            self._spinner.__enter__()

    def _finish_spinner_line(self, text: str) -> None:
        if self._spinner._enabled:
            self._stream.write(
                "\r" + (" " * (len(self._spinner._label) + 3)) + "\r")
        self._stream.write(text + "\n")
        self._stream.flush()

    def _println(self, s: str, color: str | None = None) -> None:
        line = s if color is None else ANSI.color(self._ansi, color, s)
        self._stream.write(line + "\n")
        self._stream.flush()

    def _severity_color(self, severity: Check.Severity) -> str:
        return {
            Check.Severity.INFO: ANSI.CYAN,
            Check.Severity.PASS: ANSI.GREEN,
            Check.Severity.WARN: ANSI.YELLOW,
            Check.Severity.FAIL: ANSI.RED,
        }[severity]

    @staticmethod
    def sanitize(v: Any):
        if isinstance(v, Enum):
            return v.value
        if isinstance(v, (int, float, str, bool)) or v is None:
            return v
        if isinstance(v, dict):
            return {str(k): Report.sanitize(val) for k, val in v.items()}
        if isinstance(v, list):
            return [Report.sanitize(x) for x in v]
        if isinstance(v, Variation):
            intent = getattr(v, "intent", None)
            return {
                "type": v.name,
                "intent": intent.value if isinstance(intent, Enum) else intent,
                **{k: Report.sanitize(val) for k, val in vars(v).items() if not k.startswith("_")},
            }
        return repr(v)
