from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Literal

from core import GroupCheck, Slice


class LabelsAgree(GroupCheck):
    """
    Assert that label assignments per sentence are consistent across slices.

    By default, evaluates the union of sentence ids across slices and treats missing
    annotations as the empty label set (∅). For cases where abstention is expected
    (e.g. LLM instructions allowing skipping), use scope="intersection" to evaluate
    only sentences that are annotated in all slices.
    """

    def __init__(
        self,
        *,
        warn_below: float = 0.95,
        error_below: float = 0.80,
        max_disagreements: int = 50,
        max_pairs: int = 50,
        include_pairwise: bool = False,
        scope: Literal["union", "intersection"] = "union",
    ):
        self.warn_below = float(warn_below)
        self.error_below = float(error_below)
        self.max_disagreements = int(max_disagreements)
        self.max_pairs = int(max_pairs)
        self.include_pairwise = bool(include_pairwise)
        self.scope = scope

    def check(self, slices: list[Slice]) -> tuple[GroupCheck.Severity, dict[str, Any]]:
        per_slice = {s.id: self._labels_by_sentence(s.output) for s in slices}

        # Compute which sentence ids to evaluate.
        if not per_slice:
            return GroupCheck.Severity.INFO, {
                "total_slices": 0,
                "total_sentences": 0,
                "agreement_ratio": None,
                "note": "no slices",
            }

        keys_per_slice = {sid: set(m.keys()) for sid, m in per_slice.items()}

        if self.scope == "intersection":
            sentence_ids = None
            for ids in keys_per_slice.values():
                sentence_ids = ids if sentence_ids is None else sentence_ids & ids
            sentence_ids = sentence_ids or set()
        else:  # union
            sentence_ids: set[int] = set()
            for ids in keys_per_slice.values():
                sentence_ids |= ids

        if not sentence_ids:
            return GroupCheck.Severity.INFO, {
                "total_slices": len(slices),
                "slice_ids": [s.id for s in slices],
                "total_sentences": 0,
                "agreement_ratio": None,
                "note": f"no sentence annotations found in any slice for scope={self.scope}",
                "scope": self.scope,
            }

        disagreements: list[dict[str, Any]] = []
        agreeing = 0

        for sid in sorted(sentence_ids):
            dist: Counter[str] = Counter()
            examples: dict[str, list[str]] = defaultdict(list)

            for slice_id, mapping in per_slice.items():
                # In intersection scope, sid is guaranteed to exist in mapping.
                label_set = mapping.get(sid, frozenset())
                key = self._fmt_label_set(label_set)
                dist[key] += 1
                if len(examples[key]) < 5:
                    examples[key].append(slice_id)

            if len(dist) == 1:
                agreeing += 1
                continue

            if len(disagreements) < self.max_disagreements:
                disagreements.append(
                    {
                        "sentence_id": sid,
                        "variants": dict(dist),
                        "examples": dict(examples),
                    }
                )

        total_sentences = len(sentence_ids)
        agreement_ratio = agreeing / total_sentences if total_sentences else 1.0

        severity = GroupCheck.Severity.PASS
        if agreement_ratio < self.error_below:
            severity = GroupCheck.Severity.FAIL
        elif agreement_ratio < self.warn_below:
            severity = GroupCheck.Severity.WARN

        out: dict[str, Any] = {
            "total_slices": len(slices),
            "slice_ids": [s.id for s in slices],
            "total_sentences": total_sentences,
            "agreeing_sentences": agreeing,
            "disagreeing_sentences": total_sentences - agreeing,
            "agreement_ratio": agreement_ratio,
            "warn_below": self.warn_below,
            "error_below": self.error_below,
            "disagreements": disagreements,
            "disagreements_truncated": max(0, (total_sentences - agreeing) - len(disagreements)),
            "scope": self.scope,
        }

        if self.include_pairwise:
            out["pairwise"] = self._pairwise_agreement(per_slice)

        return severity, out

    def _labels_by_sentence(self, output: Any) -> dict[int, frozenset[str]]:
        """
        Returns: sentence_id -> frozenset(label_names)
        Missing annotations produce empty mapping.
        """
        labels: dict[int, set[str]] = defaultdict(set)

        for a in self._get_annotations(output):
            try:
                start = int(a["sentence_id_start"])
                end = int(a["sentence_id_end"])
                name = a.get("code_name")
            except Exception:
                continue

            if not isinstance(name, str) or not name:
                continue

            if end < start:
                start, end = end, start

            for sid in range(start, end + 1):
                labels[sid].add(name)

        return {sid: frozenset(v) for sid, v in labels.items()}

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

    def _fmt_label_set(self, s: frozenset[str]) -> str:
        if not s:
            return "∅"
        return "{" + ", ".join(sorted(s)) + "}"

    def _pairwise_agreement(self, per_slice: dict[str, dict[int, frozenset[str]]]) -> dict[str, Any]:
        slice_ids = list(per_slice.keys())
        sentence_ids: set[int] = set()
        for m in per_slice.values():
            sentence_ids.update(m.keys())

        if not sentence_ids:
            return {"pairs": [], "note": "no sentence annotations"}

        pairs: list[dict[str, Any]] = []
        total = len(sentence_ids)

        for i in range(len(slice_ids)):
            for j in range(i + 1, len(slice_ids)):
                a_id = slice_ids[i]
                b_id = slice_ids[j]
                a = per_slice[a_id]
                b = per_slice[b_id]

                agree = 0
                for sid in sentence_ids:
                    if a.get(sid, frozenset()) == b.get(sid, frozenset()):
                        agree += 1

                if len(pairs) < self.max_pairs:
                    pairs.append(
                        {
                            "a": a_id,
                            "b": b_id,
                            "agreeing": agree,
                            "total": total,
                            "agreement_ratio": agree / total if total else 1.0,
                        }
                    )

        pairs.sort(key=lambda x: x["agreement_ratio"])
        truncated = max(
            0, (len(slice_ids) * (len(slice_ids) - 1) // 2) - len(pairs))

        return {"pairs": pairs, "pairs_truncated": truncated}
