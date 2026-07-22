"""Sparse retrieval adapters."""

from rag_pymc.domain import RetrievedChunk, SearchQuery
from rag_pymc.indexing.protocols import SparseIndex


class SparseRetriever:
    """Expose a sparse index through the common retriever contract."""

    def __init__(self, index: SparseIndex) -> None:
        """Configure the backing sparse index."""
        self._index = index

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Delegate ranking to the configured sparse index."""
        return self._index.search(query)
