from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import AnyUrl

from rag_pymc.domain import Chunk, RetrievedChunk, SearchQuery, SourceType
from rag_pymc.reranking import (
    RerankedRetriever,
    RerankingConfigurationError,
    RerankingInferenceError,
)


def make_chunk(chunk_id: str) -> Chunk:
    content = f"content for {chunk_id}"
    return Chunk(
        chunk_id=chunk_id,
        document_id=f"doc_{chunk_id}",
        library="pymc",
        library_version="6.1.0",
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl("https://example.test/source"),
        title="Test source",
        section="Test",
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        created_at=datetime(2026, 7, 20, tzinfo=UTC),
    )


class StaticRetriever:
    def __init__(self, chunks: tuple[Chunk, ...]) -> None:
        self.chunks = chunks
        self.queries: list[SearchQuery] = []

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        self.queries.append(query)
        return [
            RetrievedChunk(
                chunk=chunk,
                score=float(len(self.chunks) - rank),
                rank=rank,
                retriever="candidate",
            )
            for rank, chunk in enumerate(self.chunks[: query.top_k], start=1)
        ]


class StaticReranker:
    name = "static-reranker"
    model_id = "test/reranker"
    revision = "a" * 40

    def __init__(self, scores: tuple[float, ...]) -> None:
        self.scores = scores
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def score(self, query: str, chunks: Sequence[Chunk]) -> tuple[float, ...]:
        self.calls.append((query, tuple(chunk.chunk_id for chunk in chunks)))
        return self.scores


def test_reranked_retriever_scores_candidates_and_preserves_filters() -> None:
    chunks = tuple(make_chunk(chunk_id) for chunk_id in ("a", "b", "c", "d"))
    candidate = StaticRetriever(chunks)
    reranker = StaticReranker((0.2, 0.9, 0.5, -1.0))
    retriever = RerankedRetriever(candidate, reranker, candidate_k=4)
    query = SearchQuery(
        text="query",
        top_k=2,
        library="pymc",
        library_version="6.1.0",
        source_types=(SourceType.API_REFERENCE,),
        api_symbols=("pymc.sample",),
    )

    results = retriever.retrieve(query)

    assert [result.chunk.chunk_id for result in results] == ["b", "c"]
    assert [result.score for result in results] == [0.9, 0.5]
    assert all(result.retriever == "reranked-v1" for result in results)
    assert reranker.calls == [("query", ("a", "b", "c", "d"))]
    candidate_query = candidate.queries[0]
    assert candidate_query.top_k == 4
    assert candidate_query.library == query.library
    assert candidate_query.library_version == query.library_version
    assert candidate_query.source_types == query.source_types
    assert candidate_query.api_symbols == query.api_symbols


def test_reranked_retriever_uses_candidate_rank_for_equal_scores() -> None:
    chunks = tuple(make_chunk(chunk_id) for chunk_id in ("a", "b", "c"))
    retriever = RerankedRetriever(
        StaticRetriever(chunks),
        StaticReranker((1.0, 1.0, 1.0)),
        candidate_k=3,
    )

    results = retriever.retrieve(SearchQuery(text="query", top_k=3))

    assert [result.chunk.chunk_id for result in results] == ["a", "b", "c"]


@pytest.mark.parametrize("candidate_k", [0, -1])
def test_reranked_retriever_rejects_invalid_candidate_depth(candidate_k: int) -> None:
    with pytest.raises(RerankingConfigurationError, match="candidate_k"):
        RerankedRetriever(StaticRetriever(()), StaticReranker(()), candidate_k=candidate_k)


@pytest.mark.parametrize(
    "scores, message",
    [
        ((1.0,), "scores for 2 candidates"),
        ((1.0, float("nan")), "non-finite"),
    ],
)
def test_reranked_retriever_rejects_invalid_scores(
    scores: tuple[float, ...],
    message: str,
) -> None:
    chunks = (make_chunk("a"), make_chunk("b"))
    retriever = RerankedRetriever(
        StaticRetriever(chunks),
        StaticReranker(scores),
        candidate_k=2,
    )

    with pytest.raises(RerankingInferenceError, match=message):
        retriever.retrieve(SearchQuery(text="query", top_k=2))
