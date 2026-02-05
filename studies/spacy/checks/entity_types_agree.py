from __future__ import annotations

from itertools import combinations
from typing import Any

from core import GroupCheck, Slice


class EntityTypesAgree(GroupCheck):
    """
    Assert that extracted entity label sets are identical across slices.

    Outputs are expected to contain:
      {"entities": [{"label": "...", ...}, ...]}
    """

    def check(self, slices: list[Slice]) -> tuple[GroupCheck.Severity, dict[str, Any]]:
        by_key: dict[str, set[str]] = {}

        for s in slices:
            by_key[self._variation_key(s)] = self._entity_types(s)

        pairwise = []
        for (k1, t1), (k2, t2) in combinations(by_key.items(), 2):
            diff = sorted(t1 ^ t2)
            if diff:
                pairwise.append({"pair": [k1, k2], "diff": diff})

        severity = GroupCheck.Severity.PASS if not pairwise else GroupCheck.Severity.FAIL

        return severity, {
            "entity_types": {k: sorted(v) for k, v in by_key.items()},
            "pairwise_differences": pairwise,
            "agree": len(pairwise) == 0,
            "n_slices": len(slices),
        }

    def _entity_types(self, slice: Slice) -> set[str]:
        out = slice.output or {}
        entities = out.get("entities") or []
        types: set[str] = set()
        for e in entities:
            if isinstance(e, dict) and isinstance(e.get("label"), str):
                types.add(e["label"])
        return types

    def _variation_key(self, slice: Slice) -> str:
        v = getattr(slice, "variation", None)
        if v is None:
            return "none"
        name = getattr(v, "name", None) or v.__class__.__name__
        params = {k: val for k, val in vars(
            v).items() if not k.startswith("_")}
        return f"{name}({params})" if params else name
