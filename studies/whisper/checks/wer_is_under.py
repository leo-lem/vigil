from __future__ import annotations

from itertools import combinations
from typing import Any

from jiwer import wer

from core import GroupCheck, Slice
from lib.norm_str import norm_str


class WerIsUnder(GroupCheck):
    def __init__(self, threshold: float = 0.25, include_text: bool = False):
        self.threshold = float(threshold)
        if self.threshold <= 0:
            raise ValueError("threshold must be > 0")
        self.include_text = bool(include_text)

    def check(self, slices: list[Slice]) -> tuple[GroupCheck.Severity, dict[str, Any]]:
        if len(slices) < 2:
            return GroupCheck.Severity.INFO, {
                "n_slices": len(slices),
                "threshold": self.threshold,
                "max_wer": 0.0,
                "pairwise": [],
                "ok": True,
                "skipped": True,
            }

        texts: list[tuple[str, str]] = []
        for s in slices:
            t = self._get_transcript(s.output)
            texts.append((s.id, norm_str(t)))

        pairwise: list[dict[str, Any]] = []
        max_wer = 0.0

        for (id_a, a), (id_b, b) in combinations(texts, 2):
            score = float(wer(a, b))
            max_wer = max(max_wer, score)

            item: dict[str, Any] = {"a": id_a, "b": id_b, "wer": score}
            if self.include_text:
                item["a_text"] = a
                item["b_text"] = b
            pairwise.append(item)

        ok = max_wer <= self.threshold
        severity = GroupCheck.Severity.PASS if ok else GroupCheck.Severity.FAIL

        return severity, {
            "n_slices": len(slices),
            "threshold": self.threshold,
            "max_wer": max_wer,
            "pairwise": pairwise,
            "ok": ok,
            "skipped": False,
        }

    def _get_transcript(self, out: Any) -> str:
        if not isinstance(out, dict):
            raise TypeError("slice.output must be a dict")
        t = out.get("transcript")
        if not isinstance(t, str):
            raise KeyError("slice.output must contain 'transcript' as str")
        return t
