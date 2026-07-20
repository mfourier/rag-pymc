"""Exact in-memory cosine index for dense retrieval baselines."""

from collections.abc import Sequence

import numpy as np

from rag_pymc.domain import Chunk, RetrievedChunk, SearchQuery
from rag_pymc.embeddings import Embedder, EmbeddingMatrix
from rag_pymc.retrieval.filters import matches_filters


class DenseIndexError(Exception):
    """Raised when dense index vectors violate the index contract."""


class ExactCosineIndex:
    """Rank filtered chunks by exact cosine similarity."""

    name = "dense-cosine-v1"

    def __init__(self, chunks: Sequence[Chunk], *, embedder: Embedder) -> None:
        """Embed and normalize every chunk in deterministic corpus order."""
        self._chunks = tuple(chunks)
        self.embedder = embedder
        matrix = embedder.embed_documents([chunk.content for chunk in self._chunks])
        self._embeddings = self._normalize(
            matrix,
            expected_shape=(len(self._chunks), embedder.dimension),
        )

    def search(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Return exact cosine neighbors after applying metadata filters."""
        candidate_indices = tuple(
            index for index, chunk in enumerate(self._chunks) if matches_filters(chunk, query)
        )
        if not candidate_indices:
            return []

        query_matrix = self._normalize(
            self.embedder.embed_query(query.text),
            expected_shape=(1, self.embedder.dimension),
        )
        query_vector = query_matrix[0]
        scored = (
            (
                float(np.dot(self._embeddings[index], query_vector)),
                self._chunks[index],
            )
            for index in candidate_indices
        )
        ranked = sorted(scored, key=lambda pair: (-pair[0], pair[1].chunk_id))[: query.top_k]
        return [
            RetrievedChunk(
                chunk=chunk,
                score=score,
                rank=rank,
                retriever=self.name,
            )
            for rank, (score, chunk) in enumerate(ranked, start=1)
        ]

    @staticmethod
    def _normalize(
        matrix: EmbeddingMatrix,
        *,
        expected_shape: tuple[int, int],
    ) -> EmbeddingMatrix:
        if matrix.shape != expected_shape:
            msg = f"embedding matrix has shape {matrix.shape}, expected {expected_shape}"
            raise DenseIndexError(msg)
        if not np.isfinite(matrix).all():
            msg = "embedding matrix contains non-finite values"
            raise DenseIndexError(msg)
        if not matrix.size:
            return matrix

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        if np.any(norms <= 0):
            msg = "embedding matrix contains zero-norm vectors"
            raise DenseIndexError(msg)
        return np.asarray(matrix / norms, dtype=np.float32)
