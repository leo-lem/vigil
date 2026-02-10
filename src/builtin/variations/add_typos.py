from __future__ import annotations

from random import Random

from core import InputVariation, Input


class AddTypos(InputVariation):
    """
    Apply light typographical noise to input.data.text.

    ops:
      - swap: swap adjacent letters within a word
      - delete: delete a letter within a word
      - replace: replace a letter with a nearby keyboard-ish alternative (simple heuristic)
    """

    def __init__(
        self,
        *,
        seed: int = 0,
        ops: list[str] | None = None,
        n_edits: int = 3,
        label: str | None = None,
    ):
        self.label = label
        self.seed = int(seed)
        self.ops = ops if ops is not None else ["swap", "delete", "replace"]
        self.n_edits = int(n_edits)

    def vary(self, inputs: list[Input]):
        rng = Random(self.seed)

        if self.n_edits < 0:
            raise ValueError("n_edits must be >= 0")

        for inp in inputs:
            if not isinstance(inp, dict) or "data" not in inp or not isinstance(inp["data"], dict):
                raise TypeError(
                    "AddTypos expects inputs as dicts with a data dict.")

            data = inp["data"]
            if "text" not in data or not isinstance(data["text"], str):
                raise KeyError(
                    "AddTypos expects input.data.text to be a string.")

            text = data["text"]
            data["text"] = self._apply(text, rng)

    def _apply(self, text: str, rng: Random) -> str:
        chars = list(text)
        alpha_positions = [i for i, c in enumerate(chars) if c.isalpha()]

        if len(alpha_positions) < 2 or self.n_edits == 0:
            return text

        for _ in range(self.n_edits):
            op = rng.choice(self.ops) if self.ops else "swap"
            i = rng.choice(alpha_positions)

            if op == "swap":
                # swap with next alpha if possible
                j = i + 1
                if j < len(chars) and chars[j].isalpha():
                    chars[i], chars[j] = chars[j], chars[i]

            elif op == "delete":
                if chars[i].isalpha():
                    chars[i] = ""  # keep indices stable-ish

            elif op == "replace":
                c = chars[i]
                if c.isalpha():
                    chars[i] = self._replacement(c, rng)

            else:
                raise ValueError("ops may contain only: swap, delete, replace")

        return "".join(chars)

    def _replacement(self, c: str, rng: Random) -> str:
        # tiny heuristic: pick a vowel swap or a neighboring consonant
        vowels_lower = "aeiou"
        vowels_upper = "AEIOU"

        if c in vowels_lower:
            return rng.choice(vowels_lower)
        if c in vowels_upper:
            return rng.choice(vowels_upper)

        # consonants: shift by +/- 1 in alphabet range (still readable)
        base = ord("a") if c.islower() else ord("A")
        off = ord(c) - base
        off = max(0, min(25, off + rng.choice([-1, 1])))
        return chr(base + off)
