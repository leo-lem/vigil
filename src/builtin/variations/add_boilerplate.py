from __future__ import annotations

from random import Random

from core import InputVariation, Input


class AddBoilerplate(InputVariation):
    """
    Append boilerplate text to input.data.text.

    Intended to mimic real-world ingestion where signatures, disclaimers,
    tracking snippets, or forwarded-mail headers get attached.
    """

    DEFAULT_TEMPLATES = [
        "Sent from my iPhone",
        "Disclaimer: This message may contain confidential information.",
        "If you received this in error, please delete it and notify the sender.",
        "Unsubscribe: https://example.com/unsubscribe?id=123",
        "Read on the web: https://example.com/article?utm_source=email&utm_medium=footer",
        "-----Original Message-----",
    ]

    def __init__(
        self,
        *,
        seed: int = 0,
        templates: list[str] | None = None,
        n_lines: int = 2,
        separator: str = "\n\n",
    ):
        self.seed = int(seed)
        self.templates = templates if templates is not None else list(
            self.DEFAULT_TEMPLATES)
        self.n_lines = int(n_lines)
        self.separator = str(separator)

        if self.n_lines < 1:
            raise ValueError("n_lines must be >= 1")
        if not self.templates:
            raise ValueError("templates must be a non-empty list of strings")

    def vary(self, inputs: list[Input]):
        rng = Random(self.seed)

        for inp in inputs:
            if not isinstance(inp, dict) or "data" not in inp or not isinstance(inp["data"], dict):
                raise TypeError(
                    "AddBoilerplate expects inputs as dicts with a data dict.")

            data = inp["data"]
            if "text" not in data or not isinstance(data["text"], str):
                raise KeyError(
                    "AddBoilerplate expects input.data.text to be a string.")

            # choose unique-ish lines, but allow repeats if templates are short
            chosen: list[str] = []
            pool = list(self.templates)
            rng.shuffle(pool)

            while len(chosen) < self.n_lines:
                if pool:
                    chosen.append(pool.pop())
                else:
                    chosen.append(rng.choice(self.templates))

            boilerplate = "\n".join(chosen)
            data["text"] = f"{data['text']}{self.separator}{boilerplate}"
