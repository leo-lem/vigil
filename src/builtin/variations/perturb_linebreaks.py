from __future__ import annotations

import re
from random import Random

from core import InputVariation, Input


class PerturbLinebreaks(InputVariation):
    """
    Perturb line breaks and paragraph structure in input.data.text.

    modes:
      - insert: replace some spaces with newlines
      - remove: replace newlines with spaces
      - wrap: insert newlines to wrap long lines at approx wrap_width
    """

    def __init__(
        self,
        *,
        mode: str = "insert",
        seed: int = 0,
        intensity: float = 0.08,
        wrap_width: int = 60,
        label: str | None = None,
    ):
        self.label = label
        self.mode = str(mode)
        self.seed = int(seed)
        self.intensity = float(intensity)
        self.wrap_width = int(wrap_width)

    def vary(self, inputs: list[Input]):
        rng = Random(self.seed)

        for inp in inputs:
            if not isinstance(inp, dict) or "data" not in inp or not isinstance(inp["data"], dict):
                raise TypeError(
                    "PerturbLinebreaks expects inputs as dicts with a data dict.")

            data = inp["data"]
            if "text" not in data or not isinstance(data["text"], str):
                raise KeyError(
                    "PerturbLinebreaks expects input.data.text to be a string.")

            text = data["text"]

            if self.mode == "remove":
                # turn all linebreaks into single spaces and normalize
                text = re.sub(r"\s*\n+\s*", " ", text)
                text = re.sub(r"[ \t]+", " ", text).strip()

            elif self.mode == "insert":
                chars = list(text)
                space_positions = [i for i, c in enumerate(chars) if c == " "]
                n = int(len(space_positions) *
                        max(0.0, min(1.0, self.intensity)))
                rng.shuffle(space_positions)
                for i in sorted(space_positions[:n], reverse=True):
                    chars[i] = "\n" if rng.random() < 0.75 else "\n\n"
                text = "".join(chars)

            elif self.mode == "wrap":
                out_lines: list[str] = []
                for block in text.splitlines() or [""]:
                    line = block
                    while len(line) > self.wrap_width:
                        # break at nearest space before width, else hard break
                        cut = line.rfind(" ", 0, self.wrap_width + 1)
                        if cut <= 0:
                            cut = self.wrap_width
                        out_lines.append(line[:cut].rstrip())
                        line = line[cut:].lstrip()
                    out_lines.append(line)
                text = "\n".join(out_lines)

            else:
                raise ValueError("mode must be one of: insert, remove, wrap")

            data["text"] = text
