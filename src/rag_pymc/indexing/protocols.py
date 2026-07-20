"""Project-owned indexing interfaces."""

from typing import Protocol

from rag_pymc.domain import RetrievedChunk, SearchQuery


class SparseIndex(Protocol):
    """Search a sparse representation of the local corpus."""

    def search(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Return ranked chunks satisfying the query filters."""
        ...


class DenseIndex(Protocol):
    """Search dense vectors through a provider-neutral boundary."""

    def search(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Return ranked chunks satisfying the query filters."""
        ...
