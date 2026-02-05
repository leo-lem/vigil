from __future__ import annotations

from typing import Any

from core import ReferenceCheck, Slice


class AnnotationCountsEqual(ReferenceCheck):
    """Assert that the number of suggested annotations equals the reference slice."""

    def check(self, slice: Slice, reference: Slice) -> tuple[ReferenceCheck.Severity, dict[str, Any]]:
        ref_count = self._count(reference.output)
        other_count = self._count(slice.output)

        ok = (other_count == ref_count)
        severity = ReferenceCheck.Severity.PASS if ok else ReferenceCheck.Severity.FAIL

        return severity, {
            "input_id": slice.input_id,
            "reference_slice": reference.id,
            "slice": slice.id,
            "reference_count": ref_count,
            "slice_count": other_count,
            "matches": ok,
        }

    def _count(self, out: Any) -> int:
        try:
            results = (
                out.get("output", {})
                   .get("specific_task_result", {})
                   .get("results", [])
            )
            return int(sum(len(r.get("suggested_annotations") or []) for r in results))
        except Exception:
            return 0
