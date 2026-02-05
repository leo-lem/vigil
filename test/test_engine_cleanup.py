from __future__ import annotations

from typing import Any

from core.backend import Backend
from core.engine import Engine
from core.variation import FunctionVariation, EnvironmentVariation
from core.report import Report
from core.check import UnaryCheck, Check


class TrackingBackend(Backend):
    def __init__(self):
        self.env_applied: list[dict[str, Any]] = []
        self.fn_seen: list[dict[str, Any]] = []
        super().__init__(environment={"env": "base"}, function={"fn": "base"})

    def update_environment(self, environment: dict[str, Any]):
        self.env_applied.append(dict(environment))

    def compute(self, input: Any, function: dict[str, Any]) -> Any:
        self.fn_seen.append(dict(function))
        return {"ok": True}


class SetFn(FunctionVariation):
    def __init__(self, value: str):
        self.value = value

    def vary(self, function: dict[str, Any]) -> dict[str, Any]:
        function["fn"] = self.value
        return function


class SetEnv(EnvironmentVariation):
    def __init__(self, value: str):
        self.value = value

    def vary(self, environment: dict[str, Any]) -> dict[str, Any]:
        environment["env"] = self.value
        return environment


class AlwaysPass(UnaryCheck):
    def check(self, slice):
        return Check.Severity.PASS, {}


def test_function_and_environment_cleanup(tmp_path):
    backend = TrackingBackend()
    engine = Engine(backend)

    inputs = [{"id": "0", "data": 1}, {"id": "1", "data": 2}]
    variations = [SetFn("var"), SetEnv("var")]
    checks = [AlwaysPass()]

    spec_path = tmp_path / "spec.yml"
    spec_path.write_text(
        "hypothesis: x\ninputs: [1]\nvariations: [none]\nchecks: []\n", encoding="utf-8")

    report = Report(
        backend=backend,
        inputs=inputs,
        spec_path=spec_path,
        title="T",
        hypothesis="H",
    )

    engine.run(report=report, inputs=inputs,
               variations=variations, checks=checks)

    # FunctionVariation: function is changed during the variation and then reset at the end
    # We expect fn_seen to include "var" during the runs, and then backend.function to be back to base after the run loop.
    assert any(f.get("fn") == "var" for f in backend.fn_seen)
    assert backend.function["fn"] == "base"

    # EnvironmentVariation: update_environment is called when env changes and when it resets to base
    # Base is applied at construction, then variation applies "var", then cleanup on last input resets to base.
    assert any(e.get("env") == "var" for e in backend.env_applied)
    assert backend.environment["env"] == "base"
