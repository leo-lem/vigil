from __future__ import annotations

from random import Random

from core import InputVariation, Input


class InsertJunkCharacters(InputVariation):
    """
    Insert benign but annoying unicode characters into input.data.text.

    Intended to trigger tokenization / segmentation quirks without invalid bytes.
    """

    DEFAULT_CHARS = [
        "\u200b",  # zero width space
        "\u2060",  # word joiner
        "\u00a0",  # no-break space
        "\u202f",  # narrow no-break space
        "…",       # ellipsis
        "“", "”",  # smart quotes
    ]

    def __init__(
        self,
        *,
        seed: int = 0,
        chars: list[str] | None = None,
        count: int = 5,
        label: str | None = None,
    ):
        self.label = label
        self.seed = int(seed)
        self.chars = chars if chars is not None else list(self.DEFAULT_CHARS)
        self.count = int(count)

    def vary(self, inputs: list[Input]):
        rng = Random(self.seed)

        if not self.chars:
            raise ValueError("chars must be a non-empty list of strings")
        if self.count < 0:
            raise ValueError("count must be >= 0")

        for inp in inputs:
            if not isinstance(inp, dict) or "data" not in inp or not isinstance(inp["data"], dict):
                raise TypeError(
                    "InsertJunkCharacters expects inputs as dicts with a data dict.")

            data = inp["data"]
            if "text" not in data or not isinstance(data["text"], str):
                raise KeyError(
                    "InsertJunkCharacters expects input.data.text to be a string.")

            text = data["text"]
            if not text or self.count == 0:
                continue

            chars = list(text)
            for _ in range(self.count):
                pos = rng.randrange(0, len(chars) + 1)
                junk = rng.choice(self.chars)
                chars.insert(pos, junk)

            data["text"] = "".join(chars)
