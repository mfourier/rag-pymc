from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import AnyUrl

from rag_pymc.domain import Chunk, RetrievedChunk, SearchQuery, SourceType
from rag_pymc.retrieval import (
    FusionConfigurationError,
    ReciprocalRankFusionRetriever,
    WeightedRetriever,
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
    def __init__(self, name: str, chunks: tuple[Chunk, ...]) -> None:
        self.name = name
        self.chunks = chunks
        self.queries: list[SearchQuery] = []

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        self.queries.append(query)
        return [
            RetrievedChunk(
                chunk=chunk,
                score=float(len(self.chunks) - rank),
                rank=rank,
                retriever=self.name,
            )
            for rank, chunk in enumerate(self.chunks[: query.top_k], start=1)
        ]


def test_rrf_matches_hand_calculation_and_deduplicates_chunks() -> None:
    chunks = {chunk_id: make_chunk(chunk_id) for chunk_id in ("a", "b", "c", "d")}
    sparse = StaticRetriever("sparse", (chunks["a"], chunks["b"], chunks["c"]))
    dense = StaticRetriever("dense", (chunks["c"], chunks["b"], chunks["d"]))
    retriever = ReciprocalRankFusionRetriever(
        (
            WeightedRetriever("sparse", sparse),
            WeightedRetriever("dense", dense),
        ),
        rrf_k=60,
        candidate_k=3,
    )

    results = retriever.retrieve(SearchQuery(text="query", top_k=4))

    assert [result.chunk.chunk_id for result in results] == ["c", "b", "a", "d"]
    assert results[0].score == pytest.approx(1 / 63 + 1 / 61)
    assert results[1].score == pytest.approx(2 / 62)
    assert all(result.retriever == "weighted-rrf-v1" for result in results)


def test_rrf_passes_filters_and_candidate_depth_to_every_component() -> None:
    chunk = make_chunk("a")
    sparse = StaticRetriever("sparse", (chunk,))
    dense = StaticRetriever("dense", (chunk,))
    retriever = ReciprocalRankFusionRetriever(
        (
            WeightedRetriever("sparse", sparse, 2.0),
            WeightedRetriever("dense", dense, 1.0),
        ),
        candidate_k=8,
    )
    query = SearchQuery(
        text="query",
        top_k=2,
        library="pymc",
        library_version="6.1.0",
        source_types=(SourceType.API_REFERENCE,),
        api_symbols=("pymc.sample",),
    )

    results = retriever.retrieve(query)

    assert results[0].score == pytest.approx(3 / 61)
    for component_query in (sparse.queries[0], dense.queries[0]):
        assert component_query.top_k == 8
        assert component_query.library == query.library
        assert component_query.library_version == query.library_version
        assert component_query.source_types == query.source_types
        assert component_query.api_symbols == query.api_symbols


@pytest.mark.parametrize(
    "components",
    [
        (),
        (WeightedRetriever("only", StaticRetriever("only", ())),),
        (
            WeightedRetriever("same", StaticRetriever("first", ())),
            WeightedRetriever("same", StaticRetriever("second", ())),
        ),
    ],
)
def test_rrf_rejects_too_few_or_duplicate_components(
    components: tuple[WeightedRetriever, ...],
) -> None:
    with pytest.raises(FusionConfigurationError):
        ReciprocalRankFusionRetriever(components)


@pytest.mark.parametrize("weight", [0.0, -1.0, float("inf")])
def test_weighted_retriever_rejects_invalid_weights(weight: float) -> None:
    with pytest.raises(FusionConfigurationError, match="weight"):
        WeightedRetriever("invalid", StaticRetriever("invalid", ()), weight)
