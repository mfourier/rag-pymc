"""Tokenization policies for technical retrieval."""

import re

TECHNICAL_TOKEN_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*|\d+(?:\.\d+)*"
)


class TechnicalTokenizer:
    """Preserve Python identifiers while normalizing lexical terms."""

    name = "technical-v1"

    def tokenize(self, text: str) -> tuple[str, ...]:
        """Return case-folded technical and natural-language tokens."""
        return tuple(match.group(0).casefold() for match in TECHNICAL_TOKEN_PATTERN.finditer(text))

    def count_tokens(self, text: str) -> int:
        """Count deterministic technical-v1 accounting units in text."""
        return len(self.tokenize(text))
