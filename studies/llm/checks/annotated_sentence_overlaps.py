from __future__ import annotations

from typing import Any

from core import GroupCheck, Slice


class AnnotatedSentenceOverlaps(GroupCheck):
    """
    Assert that the set of annotated sentence ids overlaps sufficiently across slices.

    For each slice, we extract the set of sentence ids covered by suggested annotations.
    We compute:
      - union / intersection sizes
      - group-level overlap ratio: |intersection| / |union|
      - optional pairwise Jaccard overlaps

    This is designed for cases where abstention is expected and interesting (e.g. LLM
    instructions allowing skipping). It complements label agreement checks.
    """

    def __init__(
        self,
        *,
        warn_below: float = 0.90,
        error_below: float = 0.75,
        include_pairwise: bool = True,
        max_pairs: int = 50,
    ):
        self.warn_below = float(warn_below)
        self.error_below = float(error_below)
        self.include_pairwise = bool(include_pairwise)
        self.max_pairs = int(max_pairs)

    def check(self, slices: list[Slice]) -> tuple[GroupCheck.Severity, dict[str, Any]]:
        per_slice = {s.id: self._sentence_ids(s.output) for s in slices}
        slice_ids = [s.id for s in slices]

        if not per_slice:
            return GroupCheck.Severity.INFO, {
                "total_slices": 0,
                "slice_ids": [],
                "overlap_ratio": None,
                "note": "no slices",
            }

        sets = list(per_slice.values())
        union = set().union(*sets) if sets else set()
        intersection = None
        for st in sets:
            intersection = st if intersection is None else (intersection & st)
        intersection = intersection or set()

        if not union:
            # No annotations in any slice.
            return GroupCheck.Severity.INFO, {
                "total_slices": len(slices),
                "slice_ids": slice_ids,
                "overlap_ratio": None,
                "union_size": 0,
                "intersection_size": 0,
                "counts": {k: len(v) for k, v in per_slice.items()},
                "note": "no annotated sentences found in any slice",
            }

        overlap_ratio = len(intersection) / len(union)

        severity = GroupCheck.Severity.PASS
        if overlap_ratio < self.error_below:
            severity = GroupCheck.Severity.FAIL
        elif overlap_ratio < self.warn_below:
            severity = GroupCheck.Severity.WARN

        out: dict[str, Any] = {
            "total_slices": len(slices),
            "slice_ids": slice_ids,
            "counts": {k: len(v) for k, v in per_slice.items()},
            "union_size": len(union),
            "intersection_size": len(intersection),
            "overlap_ratio": overlap_ratio,
            "warn_below": self.warn_below,
            "error_below": self.error_below,
        }

        if self.include_pairwise:
            out["pairwise"] = self._pairwise_jaccard(per_slice)

        return severity, out

    def _sentence_ids(self, output: Any) -> set[int]:
        ids: set[int] = set()
        for a in self._get_annotations(output):
            try:
                start = int(a["sentence_id_start"])
                end = int(a["sentence_id_end"])
            except Exception:
                continue

            if end < start:
                start, end = end, start

            # Cover the full range; sentence annotations are typically singletons,
            # but range support is cheap and correct.
            for sid in range(start, end + 1):
                ids.add(sid)

        return ids

    def _get_annotations(self, output: Any) -> list[dict]:
        try:
            return (
                output.get("output", {})
                      .get("specific_task_result", {})
                      .get("results", [{}])[0]
                      .get("suggested_annotations", [])
            ) or []
        except Exception:
            return []

    def _pairwise_jaccard(self, per_slice: dict[str, set[int]]) -> dict[str, Any]:
        slice_ids = list(per_slice.keys())
        pairs: list[dict[str, Any]] = []

        for i in range(len(slice_ids)):
            for j in range(i + 1, len(slice_ids)):
                a_id = slice_ids[i]
                b_id = slice_ids[j]
                a = per_slice[a_id]
                b = per_slice[b_id]

                u = a | b
                inter = a & b
                ratio = (len(inter) / len(u)) if u else None

                if len(pairs) < self.max_pairs:
                    pairs.append(
                        {
                            "a": a_id,
                            "b": b_id,
                            "a_count": len(a),
                            "b_count": len(b),
                            "union": len(u),
                            "intersection": len(inter),
                            "jaccard": ratio,
                        }
                    )

        # Lowest overlap first for quick scanning
        pairs.sort(key=lambda x: (x["jaccard"] is None, x["jaccard"]))

        total_possible = len(slice_ids) * (len(slice_ids) - 1) // 2
        truncated = max(0, total_possible - len(pairs))

        return {"pairs": pairs, "pairs_truncated": truncated}
