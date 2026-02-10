import re

from core import Slice, UnaryCheck


_WORD_RE = re.compile(r"[\w']+", re.UNICODE)


class RepetitionsUnder(UnaryCheck):
    def __init__(self, threshold: int):
        self.threshold = int(threshold)

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return _WORD_RE.findall((text or "").lower())

    @staticmethod
    def _count_consecutive_token_repetitions(tokens: list[str]) -> int:
        count = 0
        for i in range(1, len(tokens)):
            if tokens[i] == tokens[i - 1]:
                count += 1
        return count

    @staticmethod
    def _count_consecutive_bigram_repetitions(tokens: list[str]) -> int:
        count = 0
        i = 0
        while i + 3 < len(tokens):
            if tokens[i] == tokens[i + 2] and tokens[i + 1] == tokens[i + 3]:
                count += 1
                i += 2
            else:
                i += 1
        return count

    def check(self, slice: Slice):
        transcript = ""
        if slice.output and isinstance(slice.output, dict):
            transcript = slice.output.get("transcript") or ""

        tokens = self._tokens(transcript)
        token_repetitions = self._count_consecutive_token_repetitions(tokens)
        bigram_repetitions = self._count_consecutive_bigram_repetitions(tokens)
        count = token_repetitions + bigram_repetitions
        severity = self.Severity.PASS if count <= self.threshold else self.Severity.FAIL

        return severity, {
            "threshold": self.threshold,
            "count": count,
            "token_repetitions": token_repetitions,
            "bigram_repetitions": bigram_repetitions,
            "n_tokens": len(tokens),
        }
