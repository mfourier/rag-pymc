from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import AnyUrl

from rag_pymc.domain import Chunk, SearchQuery, SourceType
from rag_pymc.indexing import BM25Index
from rag_pymc.retrieval import TechnicalTokenizer


def make_chunk(
    chunk_id: str,
    content: str,
    *,
    library: str = "pymc",
    version: str = "6.1.0",
    source_type: SourceType = SourceType.API_REFERENCE,
    symbols: tuple[str, ...] = ("pymc.sample",),
) -> Chunk:
    content_hash = sha256(content.encode()).hexdigest()
    return Chunk(
        chunk_id=chunk_id,
        document_id=f"doc_{chunk_id}",
        library=library,
        library_version=version,
        source_type=source_type,
        source_url=AnyUrl("https://example.test/source"),
        title="Test source",
        section="Test",
        content=content,
        content_hash=content_hash,
        api_symbols=symbols,
        created_at=datetime(2026, 7, 19, tzinfo=UTC),
    )


def test_technical_tokenizer_preserves_python_symbols() -> None:
    tokenizer = TechnicalTokenizer()

    tokens = tokenizer.tokenize("Use pymc.sample with target_accept=0.95 and pm.Data.")

    assert tokens == ("use", "pymc.sample", "with", "target_accept", "0.95", "and", "pm.data")


def test_bm25_ranks_term_frequency_and_breaks_ties_by_chunk_id() -> None:
    chunks = [
        make_chunk("chunk_c", "nuts target_accept target_accept"),
        make_chunk("chunk_b", "nuts target_accept"),
        make_chunk("chunk_a", "nuts target_accept"),
    ]
    index = BM25Index(chunks)

    results = index.search(SearchQuery(text="target_accept", top_k=3))

    assert [result.chunk.chunk_id for result in results] == ["chunk_c", "chunk_a", "chunk_b"]
    assert [result.rank for result in results] == [1, 2, 3]
    assert all(result.score > 0 for result in results)
    assert all(result.retriever == "bm25-v1" for result in results)


def test_bm25_applies_all_metadata_filters_before_ranking() -> None:
    chunks = [
        make_chunk("matching", "posterior draws"),
        make_chunk("wrong-version", "posterior draws", version="5.0.0"),
        make_chunk("wrong-library", "posterior draws", library="arviz"),
        make_chunk(
            "wrong-type",
            "posterior draws",
            source_type=SourceType.TUTORIAL,
        ),
        make_chunk("wrong-symbol", "posterior draws", symbols=("pymc.fit",)),
    ]
    query = SearchQuery(
        text="posterior",
        top_k=10,
        library="PyMC",
        library_version="6.1.0",
        source_types=(SourceType.API_REFERENCE,),
        api_symbols=("PYMC.SAMPLE",),
    )

    results = BM25Index(chunks).search(query)

    assert [result.chunk.chunk_id for result in results] == ["matching"]


def test_bm25_returns_no_results_without_lexical_overlap() -> None:
    index = BM25Index([make_chunk("chunk_a", "posterior draws")])

    assert index.search(SearchQuery(text="variational inference")) == []


@pytest.mark.parametrize(("k1", "b"), [(0.0, 0.75), (-1.0, 0.75), (1.5, -0.1), (1.5, 1.1)])
def test_bm25_rejects_invalid_parameters(k1: float, b: float) -> None:
    with pytest.raises(ValueError):
        BM25Index([], k1=k1, b=b)
