"""Project-owned context construction interfaces."""

from collections.abc import Sequence
from typing import Protocol

from rag_pymc.domain import ConstructedContext, RetrievedChunk, SearchQuery


class TokenCounter(Protocol):
    """Count deterministic accounting units for one rendered context item."""

    name: str

    def count_tokens(self, text: str) -> int:
        """Return the positive count for one nonempty rendered item."""
        ...


class ContextBuilder(Protocol):
    """Construct a bounded evidence artifact from ranked retrieval results."""

    @property
    def name(self) -> str:
        """Return the versioned builder identity."""
        ...

    @property
    def rendering_policy(self) -> str:
        """Return the versioned canonical rendering identity."""
        ...

    @property
    def truncation_policy(self) -> str:
        """Return the versioned budget-admission identity."""
        ...

    def build(
        self,
        query: SearchQuery,
        retrieved: Sequence[RetrievedChunk],
        *,
        token_budget: int,
    ) -> ConstructedContext:
        """Return deterministic complete context items within the explicit budget."""
        ...
