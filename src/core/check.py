from __future__ import annotations

from enum import Enum
from typing import Any

from .__types__ import Slice


class Check:
    """
    Abstract base class for all behavioural checks.

    A behavioural check evaluates a declared subset of slices and produces
    a structured annotation describing the observed behaviour.
    Single-slice evaluation is treated as the degenerate case.
    """
    intent: Check.Intent

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def evaluate(self, slices: list[Slice], references: list[Slice]) -> tuple[Check.Severity, dict[str, Any]]:
        """ Evaluate the check over a subset of slices, possibly using reference slices. """
        raise NotImplementedError

    class Intent(str, Enum):
        """
        Declares the behavioural intent of a check.

        - UNARY: operates on a single slice
        - REFERENCE: operates on a single slice comparing to reference behaviour
        - GROUP: operates on two or more slices
        """
        UNARY = "unary"
        REFERENCE = "reference"
        GROUP = "group"

    class Severity(Enum):
        """
        Declares the severity level of a check result.

        - INFO: informational outcome, does not affect run status
        - PASS: passing outcome, marks run as successful
        - WARN: warning outcome, marks run as warned
        - FAILURE: error outcome, fails the check and the run
        """
        INFO = 0
        PASS = 1
        WARN = 2
        FAIL = 3

        @staticmethod
        def merge(severities: list[Check.Severity]) -> Check.Severity:
            """ Merge multiple severity levels into a single representative level. """
            return max(severities, key=lambda s: s.value) if severities else Check.Severity.INFO

        @property
        def label(self) -> str:
            return self.name.lower()

        @property
        def icon(self) -> str:
            return {
                Check.Severity.INFO: "i",
                Check.Severity.PASS: "✔",
                Check.Severity.WARN: "⚠",
                Check.Severity.FAIL: "✖",
            }[self]


class UnaryCheck(Check):
    """
    Evaluates one slice at a time.

    If multiple slices are provided, the check is applied per-slice and the
    results are merged into a single (severity, annotation) pair.
    """

    intent = Check.Intent.UNARY

    def evaluate(self, slices: list[Slice], references: list[Slice]) -> tuple[Check.Severity, dict[str, Any]]:
        _ = references  # unary checks do not use references
        if not slices:
            raise ValueError("Unary checks require at least one slice.")

        severities: list[Check.Severity] = []
        result: dict[str, Any] = {}

        for slice in slices:
            severity, annotation = self.check(slice)
            severities.append(severity)

            result[slice.id] = {
                "severity": severity.label, **(annotation or {})}

        return Check.Severity.merge(severities), result

    def check(self, slice: Slice) -> tuple[Check.Severity, dict[str, Any]]:
        raise NotImplementedError


class ReferenceCheck(Check):
    """
    Evaluates each slice against a corresponding baseline slice.

    Reference checks operate on pairs of slices: one baseline slice and one
    variation slice. The check compares the behaviour of the variation slice
    against the baseline slice and produces a severity and annotation per pair.
    """
    intent = Check.Intent.REFERENCE

    def evaluate(self, slices: list[Slice], references: list[Slice]) -> tuple[Check.Severity, dict[str, Any]]:
        if not slices:
            raise ValueError("Reference checks require at least one slice.")
        if len(slices) != len(references):
            raise ValueError(
                f"Mismatched number of slices and reference slices: {len(slices)} != {len(references)}")

        severities: list[Check.Severity] = []
        result: dict[str, Any] = {}

        for slice, reference in zip(slices, references):
            if slice.input_id != reference.input_id:
                raise ValueError(
                    f"Mismatched slice/reference alignment: input_id {slice.input_id} != {reference.input_id}")
            severity, annotation = self.check(slice, reference)
            severities.append(severity)
            result[slice.id] = {
                "severity": severity.label, **(annotation or {})}

        return Check.Severity.merge(severities), result

    def check(self, slice: Slice, reference: Slice) -> tuple[Check.Severity, dict[str, Any]]:
        raise NotImplementedError


class GroupCheck(Check):
    """
    Behavioural check that evaluates a relation across a set of slices.

    Group checks operate on two or more non-baseline slices and return
    a single merged outcome.
    """
    intent = Check.Intent.GROUP

    def evaluate(self, slices: list[Slice], references: list[Slice]) -> tuple[Check.Severity, dict[str, Any]]:
        _ = references

        if not slices:
            raise ValueError("Group checks require at least one slice.")

        groups: dict[str, list[Slice]] = {}
        for s in slices:
            groups.setdefault(str(s.input_id), []).append(s)

        severities: list[Check.Severity] = []
        results: dict[str, Any] = {}

        skipped: list[str] = []

        for input_id, group in groups.items():
            if len(group) < 2:
                skipped.append(input_id)
                continue

            severity, annotation = self.check(group)
            severities.append(severity)
            results[input_id] = {
                "severity": severity.label,
                **(annotation or {})
            }

        merged = Check.Severity.merge(
            severities) if severities else Check.Severity.INFO

        out: dict[str, Any] = {
            "groups": results,
            "n_groups": len(results),
            "skipped": skipped,
            "n_skipped": len(skipped),
        }

        return merged, out

    def check(self, slices: list[Slice]) -> tuple[Check.Severity, dict[str, Any]]:
        raise NotImplementedError
