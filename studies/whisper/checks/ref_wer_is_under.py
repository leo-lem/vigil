from __future__ import annotations

from typing import Any

from jiwer import wer

from core import ReferenceCheck, Slice
from lib.norm_str import norm_str


class RefWerUnder(ReferenceCheck):
    """
    Check that word error rate stays under a threshold.

    Compares slice.output["transcript"] to reference.output["transcript"] (or ["reference"]).
    """

    def __init__(self, threshold: float = 0.25):
        self.threshold = float(threshold)
        if self.threshold <= 0:
            raise ValueError("threshold must be > 0")

    def check(self, slice: Slice, reference: Slice) -> tuple[ReferenceCheck.Severity, dict[str, Any]]:
        hyp = self._get_transcript(slice.output, "slice")
        ref = self._get_reference_transcript(reference.output)

        ref_norm = norm_str(ref)
        hyp_norm = norm_str(hyp)

        score = float(wer(ref_norm, hyp_norm))
        ok = score <= self.threshold

        return (
            ReferenceCheck.Severity.PASS if ok else ReferenceCheck.Severity.FAIL,
            {
                "input_id": slice.input_id,
                "wer": score,
                "threshold": self.threshold,
                "ok": ok,
                "reference_timestamp": reference.timestamp,
                "slice_timestamp": slice.timestamp,
            },
        )

    def _get_transcript(self, out: Any, which: str) -> str:
        if not isinstance(out, dict):
            raise TypeError(f"{which}.output must be a dict")
        t = out.get("transcript")
        if not isinstance(t, str):
            raise KeyError(f"{which}.output must contain 'transcript' as str")
        return t

    def _get_reference_transcript(self, out: Any) -> str:
        if not isinstance(out, dict):
            raise TypeError("reference.output must be a dict")

        t = out.get("transcript")
        if isinstance(t, str):
            return t

        t2 = out.get("reference")
        if isinstance(t2, str):
            return t2

        raise KeyError(
            "reference.output must contain 'transcript' or 'reference' as str")
