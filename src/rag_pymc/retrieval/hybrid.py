"""Rank-based hybrid retrieval with explicit reciprocal-rank fusion."""

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from rag_pymc.domain import Chunk, RetrievedChunk, SearchQuery
from rag_pymc.retrieval.protocols import Retriever


class FusionConfigurationError(ValueError):
    """Raised when a fusion configuration is not meaningful."""


@dataclass(frozen=True, slots=True)
class WeightedRetriever:
    """One named retrieval component and its positive fusion weight."""

    name: str
    retriever: Retriever
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate component identity and weight."""
        if not self.name.strip():
            msg = "retriever component name must not be empty"
            raise FusionConfigurationError(msg)
        if not math.isfinite(self.weight) or self.weight <= 0:
            msg = "retriever component weight must be finite and greater than zero"
            raise FusionConfigurationError(msg)


class ReciprocalRankFusionRetriever:
    """Fuse component ranks without comparing implementation-specific scores."""

    name = "weighted-rrf-v1"

    def __init__(
        self,
        components: Sequence[WeightedRetriever],
        *,
        rrf_k: int = 60,
        candidate_k: int = 10,
    ) -> None:
        """Configure deterministic weighted Reciprocal Rank Fusion."""
        if len(components) < 2:
            msg = "reciprocal-rank fusion requires at least two retrievers"
            raise FusionConfigurationError(msg)
        names = [component.name for component in components]
        if len(set(names)) != len(names):
            msg = "retriever component names must be unique"
            raise FusionConfigurationError(msg)
        if rrf_k < 1:
            msg = "rrf_k must be greater than zero"
            raise FusionConfigurationError(msg)
        if candidate_k < 1:
            msg = "candidate_k must be greater than zero"
            raise FusionConfigurationError(msg)

        self.components = tuple(components)
        self.rrf_k = rrf_k
        self.candidate_k = candidate_k

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Retrieve component candidates and return their fused ranking."""
        candidate_query = query.model_copy(update={"top_k": max(query.top_k, self.candidate_k)})
        scores: defaultdict[str, float] = defaultdict(float)
        chunks: dict[str, Chunk] = {}

        for component in self.components:
            seen: set[str] = set()
            for rank, result in enumerate(
                component.retriever.retrieve(candidate_query)[: self.candidate_k],
                start=1,
            ):
                chunk_id = result.chunk.chunk_id
                if chunk_id in seen:
                    continue
                seen.add(chunk_id)
                existing = chunks.get(chunk_id)
                if existing is not None and existing != result.chunk:
                    msg = f"retrievers returned conflicting chunks for {chunk_id}"
                    raise FusionConfigurationError(msg)
                chunks[chunk_id] = result.chunk
                scores[chunk_id] += component.weight / (self.rrf_k + rank)

        ranked_ids = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))[
            : query.top_k
        ]
        return [
            RetrievedChunk(
                chunk=chunks[chunk_id],
                score=scores[chunk_id],
                rank=rank,
                retriever=self.name,
            )
            for rank, chunk_id in enumerate(ranked_ids, start=1)
        ]
