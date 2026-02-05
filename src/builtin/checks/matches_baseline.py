from __future__ import annotations

from difflib import unified_diff
from json import dumps

from core import ReferenceCheck, Slice


class MatchesBaseline(ReferenceCheck):
    """Assert slice output equals reference output; include a short diff on mismatch."""

    def __init__(self, include_diff: bool = True, max_lines: int = 200):
        self.include_diff = bool(include_diff)
        self.max_lines = int(max_lines)

    def check(self, slice: Slice, reference: Slice) -> tuple[ReferenceCheck.Severity, dict]:
        if slice.output == reference.output:
            return ReferenceCheck.Severity.PASS, {
                "input_id": slice.input_id,
                "matched": True,
            }

        ann: dict = {
            "input_id": slice.input_id,
            "matched": False,
            "reference_timestamp": reference.timestamp,
            "slice_timestamp": slice.timestamp,
        }

        if self.include_diff:
            base = self._norm_json(reference.output)
            other = self._norm_json(slice.output)

            diff = [line.rstrip("\n") for line in unified_diff(
                base,
                other,
                fromfile="reference",
                tofile="slice",
                lineterm="",
            )]

            ann["diff"] = diff[: self.max_lines]
            ann["diff_truncated"] = len(diff) > self.max_lines

        return ReferenceCheck.Severity.FAIL, ann

    def _norm_json(self, x) -> list[str]:
        return dumps(
            x,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ).splitlines(keepends=True)
