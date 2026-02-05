from __future__ import annotations

from pathlib import Path

from core.spec import Specification


def write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_spec_env_injects_params(tmp_path: Path, monkeypatch):
    write(
        tmp_path / "checks" / "needs_env_check.py",
        """
class NeedsEnv:
    def __init__(self, threshold):
        self.threshold = threshold
""".lstrip(),
    )

    write(
        tmp_path / "spec.yml",
        """
hypothesis: Env works
inputs: [1]
variations: [none]
checks:
  - type: needs_env
""".lstrip(),
    )

    # your loader tries plain param name first, then VIGIL_PARAM
    monkeypatch.setenv("threshold", "123")  # loads() -> int 123

    spec = Specification(str(tmp_path / "spec.yml"), default_title="X")
    chk = spec.checks[0]
    assert getattr(chk, "threshold") == 123
