"""Dense retrieval adapters."""

from rag_pymc.domain import RetrievedChunk, SearchQuery
from rag_pymc.indexing.protocols import DenseIndex


class DenseRetriever:
    """Expose a dense index through the common retriever contract."""

    def __init__(self, index: DenseIndex) -> None:
        """Configure the backing dense index."""
        self._index = index

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Delegate ranking to the configured dense index."""
        return self._index.search(query)
