"""Project-owned retrieval interfaces."""

from typing import Protocol

from rag_pymc.domain import RetrievedChunk, SearchQuery


class Retriever(Protocol):
    """Rank chunks for a validated search query."""

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Return ranked chunks in descending relevance order."""
        ...
