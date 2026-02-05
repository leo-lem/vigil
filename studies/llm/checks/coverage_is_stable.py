from __future__ import annotations

from typing import Any

from core import ReferenceCheck, Slice


class CoverageIsStable(ReferenceCheck):
    """Assert that the set of covered sentence ids matches the reference slice."""

    def check(self, slice: Slice, reference: Slice) -> tuple[ReferenceCheck.Severity, dict[str, Any]]:
        ref = self._covered(reference.output)
        other = self._covered(slice.output)

        missing = sorted(ref - other)
        extra = sorted(other - ref)

        ok = (not missing and not extra)
        severity = ReferenceCheck.Severity.PASS if ok else ReferenceCheck.Severity.FAIL

        return severity, {
            "input_id": slice.input_id,
            "reference_slice": reference.id,
            "slice": slice.id,
            "matches": ok,
            "missing": missing,
            "extra": extra,
            "reference_count": len(ref),
            "slice_count": len(other),
        }

    def _covered(self, output: Any) -> set[int]:
        sids: set[int] = set()
        for a in self._get_annotations(output):
            try:
                start = int(a["sentence_id_start"])
                end = int(a["sentence_id_end"])
            except Exception:
                continue

            if end < start:
                start, end = end, start

            sids.update(range(start, end + 1))
        return sids

    def _get_annotations(self, output: Any) -> list[dict]:
        try:
            return output["output"]["specific_task_result"]["results"][0].get("suggested_annotations", [])
        except Exception:
            return []
