"""Project-owned reranking interface."""

from collections.abc import Sequence
from typing import Protocol

from rag_pymc.domain import Chunk


class Reranker(Protocol):
    """Assign one comparable relevance score to each query-chunk pair."""

    name: str
    model_id: str
    revision: str

    def score(self, query: str, chunks: Sequence[Chunk]) -> tuple[float, ...]:
        """Return one finite score per chunk in input order."""
        ...
