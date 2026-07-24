from datetime import UTC, datetime, timedelta

import pytest
from pydantic import AnyUrl, ValidationError

from rag_pymc.domain import Document, RetrievedChunk, SearchQuery, SourceType
from tests.factories import make_chunk

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
HASH = "a" * 64


def test_document_preserves_provenance() -> None:
    document = Document(
        document_id="document_001",
        library="pymc",
        library_version="6.1.0",
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl(
            "https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html"
        ),
        title="pymc.sample",
        content="Normalized API reference content.",
        content_hash=HASH,
        fetched_at=NOW,
        source_commit="56384e5afed6d1ad122e19b1bf3a7885fc38e5e5",
        license_name="Apache-2.0",
        license_url=AnyUrl("https://github.com/pymc-devs/pymc/blob/v6.1.0/LICENSE"),
    )

    assert document.library_version == "6.1.0"
    assert str(document.source_url).startswith("https://www.pymc.io/")


def test_chunk_rejects_invalid_hash() -> None:
    with pytest.raises(ValidationError, match="content_hash"):
        make_chunk(content_hash="not-a-sha256")


def test_chunk_rejects_indexing_before_creation() -> None:
    with pytest.raises(ValidationError, match="indexed_at must not be earlier"):
        make_chunk(indexed_at=NOW - timedelta(seconds=1))


def test_search_query_validates_top_k_and_normalizes_text() -> None:
    query = SearchQuery(text="  How does pymc.sample work?  ", top_k=5, library="pymc")

    assert query.text == "How does pymc.sample work?"
    assert query.top_k == 5

    with pytest.raises(ValidationError, match="less than or equal to 100"):
        SearchQuery(text="query", top_k=101)


def test_retrieved_chunk_composes_rank_and_score() -> None:
    result = RetrievedChunk(chunk=make_chunk(), score=7.25, rank=1, retriever="bm25")

    assert result.chunk.chunk_id == "chunk_001"
    assert result.score == pytest.approx(7.25)
    assert result.rank == 1


def test_domain_models_are_immutable() -> None:
    query = SearchQuery(text="What is observed?", top_k=3)

    with pytest.raises(ValidationError, match="frozen"):
        query.top_k = 4
