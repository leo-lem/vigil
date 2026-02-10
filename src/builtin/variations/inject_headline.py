from __future__ import annotations

from random import Random

from core import InputVariation, Input


class InjectHeadline(InputVariation):
    """
    Prepend a short headline / boilerplate line to input.data.text.
    Intended to mimic scraped or formatted documents.
    """

    DEFAULT_TEMPLATES = [
        "Breaking: Product feedback report",
        "Customer Review Summary",
        "Excerpt",
        "Internal Memo",
        "Published on 2026-02-10",
        "Read more: https://example.com",
    ]

    def __init__(
        self,
        *,
        seed: int = 0,
        templates: list[str] | None = None,
        separator: str = "\n\n",
        label: str | None = None,
    ):
        self.label = label
        self.seed = int(seed)
        self.templates = templates if templates is not None else list(
            self.DEFAULT_TEMPLATES)
        self.separator = str(separator)

    def vary(self, inputs: list[Input]):
        rng = Random(self.seed)

        if not self.templates:
            raise ValueError("templates must be a non-empty list of strings")

        for inp in inputs:
            if not isinstance(inp, dict) or "data" not in inp or not isinstance(inp["data"], dict):
                raise TypeError(
                    "InjectHeadline expects inputs as dicts with a data dict.")

            data = inp["data"]
            if "text" not in data or not isinstance(data["text"], str):
                raise KeyError(
                    "InjectHeadline expects input.data.text to be a string.")

            headline = rng.choice(self.templates)
            data["text"] = f"{headline}{self.separator}{data['text']}"
