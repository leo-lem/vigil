import re


def norm_str(s: str) -> str:
    """Normalize a string for comparison purposes."""

    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())
