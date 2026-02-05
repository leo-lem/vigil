from __future__ import annotations

from typing import Any

from core import UnaryCheck, Slice


class Summary(UnaryCheck):
    """Record raw output of a slice."""

    def __init__(self, *, max_items: int | None = None):
        self.max_items = max_items

    def check(self, slice: Slice) -> tuple[UnaryCheck.Severity, dict[str, Any]]:
        out = slice.output

        if self.max_items is not None:
            try:
                items = list(out.items())[: self.max_items]
                out = dict(items)
                truncated = True
            except Exception:
                truncated = False
        else:
            truncated = False

        return UnaryCheck.Severity.INFO, {
            "slice_id": slice.id,
            "output": out,
            "truncated": truncated,
        }
