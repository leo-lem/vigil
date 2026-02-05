from __future__ import annotations

from copy import deepcopy
from time import time

from .__types__ import Input, Slice
from .backend import Backend
from .check import Check
from .report import Report
from .variation import Variation


class Engine:
    def __init__(self, backend: Backend):
        self.backend = backend

    def run(
        self,
        report: Report,
        inputs: list[Input],
        variations: list[Variation | None],
        checks: list[Check],
    ) -> Report:
        references_by_input_id = self._build_references(inputs)

        all_slices: list[Slice] = []

        total_variations = len(variations)
        for variation_index, variation in enumerate(variations):
            report.start_variation(
                variation_index, total_variations, variation)

            start_time = time()
            applied_inputs = inputs if variation is None else list(
                variation.apply(inputs, self.backend)
            )

            slices = self._run_variation(applied_inputs, variation)
            duration_s = time() - start_time

            report.finish_variation(
                variation_index,
                total_variations,
                variation,
                n_inputs=len(applied_inputs),
                duration_s=duration_s,
            )

            all_slices.extend(slices)

        total_checks = len(checks)
        for check_index, check in enumerate(checks):
            report.start_check(check_index, total_checks, check.name)

            intent = getattr(check, "intent", None)
            if intent == Check.Intent.REFERENCE:
                references = [references_by_input_id[slice.input_id]
                              for slice in all_slices]
            else:
                references = []

            severity, annotation = check.evaluate(all_slices, references)
            report.finish_check(check.name, severity, annotation or {})

        return report

    def _build_references(self, inputs: list[Input]) -> dict[str, Slice]:
        references: dict[str, Slice] = {}

        for input in inputs:
            reference_output = input.get("reference")

            function_snapshot = deepcopy(self.backend.function)
            environment_snapshot = deepcopy(self.backend.environment)

            output = (
                deepcopy(reference_output)
                if reference_output is not None
                else self.backend.run(
                    input["data"],
                    cleanup_env=True,
                    cleanup_fn=True,
                )
            )

            references[input["id"]] = Slice(
                input=input,
                output=output,
                function=function_snapshot,
                environment=environment_snapshot,
                variation=None,
                meta={
                    "source": "provided" if reference_output is not None else "executed"},
            )

        return references

    def _run_variation(self, inputs: list[Input], variation: Variation | None) -> list[Slice]:
        intent = None if variation is None else getattr(
            variation, "intent", None)
        total_inputs = len(inputs)

        slices: list[Slice] = []

        for input_index, input in enumerate(inputs):
            is_last_input = (input_index == total_inputs - 1)

            cleanup_function = bool(
                is_last_input and intent == Variation.Intent.FUNCTION)
            cleanup_environment = bool(
                is_last_input and intent == Variation.Intent.ENVIRONMENT)

            function_snapshot = deepcopy(self.backend.function)
            environment_snapshot = deepcopy(self.backend.environment)

            output = self.backend.run(
                input["data"],
                cleanup_env=cleanup_environment,
                cleanup_fn=cleanup_function,
            )

            slices.append(
                Slice(
                    input=input,
                    output=output,
                    function=function_snapshot,
                    environment=environment_snapshot,
                    variation=variation
                )
            )

        return slices
