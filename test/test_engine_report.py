from __future__ import annotations

from pathlib import Path
from typing import Any
from yaml import safe_load

from core.backend import Backend
from core.engine import Engine
from core.report import Report
from core.check import UnaryCheck, Check


class DummyBackend(Backend):
    def __init__(self):
        super().__init__(environment={"env": "base"}, function={"fn": "base"})
        self.applied_env: dict[str, Any] | None = None

    def update_environment(self, environment: dict[str, Any]):
        # engine expects this to exist and be side-effectful
        self.applied_env = dict(environment)

    def compute(self, input: Any, function: dict[str, Any]) -> Any:
        # deterministic "observable output"
        return {"input": input, "function": dict(function), "environment": dict(self.environment)}


class OutputHasKeys(UnaryCheck):
    def check(self, slice):
        out = slice.output
        ok = isinstance(out, dict) and {
            "input", "function", "environment"} <= set(out.keys())
        return (Check.Severity.PASS if ok else Check.Severity.FAIL, {"ok": ok})


def test_engine_runs_and_writes_report(tmp_path: Path):
    backend = DummyBackend()
    engine = Engine(backend)

    spec_path = tmp_path / "spec.yml"
    spec_path.write_text(
        "hypothesis: test\ninputs: [1]\nvariations: [none]\nchecks: []\n", encoding="utf-8")

    inputs = [{"id": "0", "data": 1}]
    variations = [None]
    checks = [OutputHasKeys()]

    report = Report(
        backend=backend,
        inputs=inputs,
        spec_path=spec_path,
        title="Test",
        hypothesis="Hypothesis",
    )

    engine.run(report=report, inputs=inputs,
               variations=variations, checks=checks)
    out_path = report.write()

    assert out_path.is_file()

    data = safe_load(out_path.read_text(encoding="utf-8"))
    assert data["meta"]["title"] == "Test"
    assert data["backend"]["type"] == "DummyBackend"
    assert len(data["variations"]) == 1
    assert len(data["checks"]) == 1
