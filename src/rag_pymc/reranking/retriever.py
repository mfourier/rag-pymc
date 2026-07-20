"""Retriever adapter that reranks a bounded candidate list."""

import math
from collections.abc import Sequence

from rag_pymc.domain import Chunk, RetrievedChunk, SearchQuery
from rag_pymc.reranking.errors import (
    RerankingConfigurationError,
    RerankingInferenceError,
)
from rag_pymc.reranking.protocols import Reranker
from rag_pymc.retrieval.protocols import Retriever


class RerankedRetriever:
    """Rerank candidates while preserving query filters and domain models."""

    name = "reranked-v1"

    def __init__(
        self,
        candidate_retriever: Retriever,
        reranker: Reranker,
        *,
        candidate_k: int = 10,
    ) -> None:
        """Configure a bounded deterministic reranking stage."""
        if candidate_k < 1:
            msg = "candidate_k must be greater than zero"
            raise RerankingConfigurationError(msg)
        self.candidate_retriever = candidate_retriever
        self.reranker = reranker
        self.candidate_k = candidate_k

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        """Retrieve candidates, score query-chunk pairs, and return the top results."""
        candidate_query = query.model_copy(update={"top_k": max(query.top_k, self.candidate_k)})
        raw_candidates = self.candidate_retriever.retrieve(candidate_query)[: self.candidate_k]
        candidates = self._deduplicate(raw_candidates)
        if not candidates:
            return []

        scores = self.reranker.score(
            query.text,
            tuple(candidate.chunk for candidate in candidates),
        )
        if len(scores) != len(candidates):
            msg = f"reranker returned {len(scores)} scores for {len(candidates)} candidates"
            raise RerankingInferenceError(msg)
        if not all(math.isfinite(score) for score in scores):
            msg = "reranker returned non-finite scores"
            raise RerankingInferenceError(msg)

        ranked = sorted(
            zip(scores, candidates, strict=True),
            key=lambda item: (-item[0], item[1].rank, item[1].chunk.chunk_id),
        )[: query.top_k]
        return [
            RetrievedChunk(
                chunk=candidate.chunk,
                score=score,
                rank=rank,
                retriever=self.name,
            )
            for rank, (score, candidate) in enumerate(ranked, start=1)
        ]

    @staticmethod
    def _deduplicate(candidates: Sequence[RetrievedChunk]) -> tuple[RetrievedChunk, ...]:
        unique: list[RetrievedChunk] = []
        chunks: dict[str, Chunk] = {}
        for candidate in candidates:
            chunk_id = candidate.chunk.chunk_id
            existing = chunks.get(chunk_id)
            if existing is not None:
                if existing != candidate.chunk:
                    msg = f"candidate retriever returned conflicting chunks for {chunk_id}"
                    raise RerankingInferenceError(msg)
                continue
            chunks[chunk_id] = candidate.chunk
            unique.append(candidate)
        return tuple(unique)
