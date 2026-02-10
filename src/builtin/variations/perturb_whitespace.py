from __future__ import annotations

import re
from random import Random

from core import InputVariation, Input


class PerturbWhitespace(InputVariation):
    """
    Perturb whitespace in input.data.text without changing semantic content.

    modes:
      - collapse: collapse runs of spaces/tabs to a single space (preserve newlines)
      - expand: add extra spaces around existing spaces
      - tabs: replace some spaces with tabs
    """

    def __init__(
        self,
        *,
        mode: str = "collapse",
        seed: int = 0,
        intensity: float = 0.15,
        label: str | None = None,
    ):
        self.label = label
        self.mode = str(mode)
        self.seed = int(seed)
        self.intensity = float(intensity)

    def vary(self, inputs: list[Input]):
        rng = Random(self.seed)

        for inp in inputs:
            if not isinstance(inp, dict) or "data" not in inp or not isinstance(inp["data"], dict):
                raise TypeError(
                    "PerturbWhitespace expects inputs as dicts with a data dict.")

            data = inp["data"]
            if "text" not in data or not isinstance(data["text"], str):
                raise KeyError(
                    "PerturbWhitespace expects input.data.text to be a string.")

            text = data["text"]

            if self.mode == "collapse":
                # collapse spaces and tabs, keep newlines
                text = re.sub(r"[ \t]+", " ", text)

            elif self.mode == "expand":
                # add extra spaces at some existing space positions
                chars = list(text)
                space_positions = [i for i, c in enumerate(chars) if c == " "]
                n = int(len(space_positions) *
                        max(0.0, min(1.0, self.intensity)))
                rng.shuffle(space_positions)
                for i in sorted(space_positions[:n], reverse=True):
                    extra = " " * (2 if rng.random() < 0.7 else 3)
                    chars.insert(i, extra)
                text = "".join(chars)

            elif self.mode == "tabs":
                chars = list(text)
                space_positions = [i for i, c in enumerate(chars) if c == " "]
                n = int(len(space_positions) *
                        max(0.0, min(1.0, self.intensity)))
                rng.shuffle(space_positions)
                for i in space_positions[:n]:
                    chars[i] = "\t"
                text = "".join(chars)

            else:
                raise ValueError("mode must be one of: collapse, expand, tabs")

            data["text"] = text
