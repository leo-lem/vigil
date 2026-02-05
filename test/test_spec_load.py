from __future__ import annotations

from pathlib import Path

from core.spec import Specification


def write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_spec_loads_project_components(tmp_path: Path):
    # project layout that your spec loader searches
    write(
        tmp_path / "checks" / "dummy_check.py",
        """
class Dummy:
    def __init__(self):
        pass
""".lstrip(),
    )

    write(
        tmp_path / "variations" / "dummy_variation.py",
        """
class Dummy:
    def __init__(self):
        pass
""".lstrip(),
    )

    write(
        tmp_path / "spec.yml",
        """
title: Test Spec
hypothesis: Works
inputs:
  - 123
variations:
  - dummy
checks:
  - dummy
""".lstrip(),
    )

    spec = Specification(str(tmp_path / "spec.yml"), default_title="Default")
    assert spec.title == "Test Spec"
    assert spec.hypothesis == "Works"
    assert spec.inputs and spec.inputs[0]["data"] == 123

    # Variation list contains instantiated objects (or None)
    assert spec.variations
    assert spec.variations[0] is not None
    assert spec.variations[0].__class__.__name__ == "Dummy"

    # Checks list contains instantiated objects
    assert spec.checks
    assert spec.checks[0].__class__.__name__ == "Dummy"
