import re

from text_unidecode import unidecode

WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    cleaned = unidecode(value or "")
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def excerpt(text: str, max_length: int = 220) -> str:
    normalized = normalize_text(text)
    if len(normalized) <= max_length:
        return normalized
    snippet = normalized[: max_length - 3].rsplit(" ", 1)[0]
    return f"{snippet}..."

