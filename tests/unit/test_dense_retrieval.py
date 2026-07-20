from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest
from pydantic import AnyUrl

from rag_pymc.domain import Chunk, SearchQuery, SourceType
from rag_pymc.embeddings import EmbeddingMatrix, load_embedding_model_spec
from rag_pymc.indexing import DenseIndexError, ExactCosineIndex


class FakeEmbedder:
    name = "fake-embedder"
    model_id = "fake/model"
    revision = "a" * 40
    dimension = 2

    def __init__(
        self,
        document_vectors: dict[str, tuple[float, float]],
        query_vectors: dict[str, tuple[float, float]],
    ) -> None:
        self._document_vectors = document_vectors
        self._query_vectors = query_vectors
        self.query_calls = 0

    def embed_documents(self, texts: Sequence[str]) -> EmbeddingMatrix:
        return np.asarray([self._document_vectors[text] for text in texts], dtype=np.float32)

    def embed_query(self, text: str) -> EmbeddingMatrix:
        self.query_calls += 1
        return np.asarray([self._query_vectors[text]], dtype=np.float32)


def make_chunk(
    chunk_id: str,
    content: str,
    *,
    version: str = "6.1.0",
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id=f"doc_{chunk_id}",
        library="pymc",
        library_version=version,
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl("https://example.test/source"),
        title="Test source",
        section="Test",
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        api_symbols=("pymc.sample",),
        created_at=datetime(2026, 7, 19, tzinfo=UTC),
    )


def test_exact_cosine_index_ranks_similarity_and_breaks_ties_by_id() -> None:
    chunks = [
        make_chunk("chunk_b", "same"),
        make_chunk("chunk_a", "same"),
        make_chunk("chunk_c", "diagonal"),
        make_chunk("chunk_d", "orthogonal"),
    ]
    embedder = FakeEmbedder(
        document_vectors={
            "same": (1.0, 0.0),
            "diagonal": (1.0, 1.0),
            "orthogonal": (0.0, 1.0),
        },
        query_vectors={"target": (1.0, 0.0)},
    )

    results = ExactCosineIndex(chunks, embedder=embedder).search(
        SearchQuery(text="target", top_k=4)
    )

    assert [result.chunk.chunk_id for result in results] == [
        "chunk_a",
        "chunk_b",
        "chunk_c",
        "chunk_d",
    ]
    assert results[0].score == pytest.approx(1.0)
    assert results[2].score == pytest.approx(2**-0.5)
    assert results[3].score == pytest.approx(0.0)


def test_dense_index_filters_before_embedding_the_query() -> None:
    chunks = [make_chunk("current", "current"), make_chunk("old", "old", version="5.0.0")]
    embedder = FakeEmbedder(
        document_vectors={"current": (1.0, 0.0), "old": (0.0, 1.0)},
        query_vectors={"query": (1.0, 0.0)},
    )
    index = ExactCosineIndex(chunks, embedder=embedder)

    no_candidates = index.search(
        SearchQuery(text="query", library="arviz", library_version="1.0.0")
    )
    current = index.search(SearchQuery(text="query", library_version="6.1.0"))

    assert no_candidates == []
    assert embedder.query_calls == 1
    assert [result.chunk.chunk_id for result in current] == ["current"]


def test_dense_index_rejects_zero_norm_document_vectors() -> None:
    embedder = FakeEmbedder(
        document_vectors={"zero": (0.0, 0.0)},
        query_vectors={"query": (1.0, 0.0)},
    )

    with pytest.raises(DenseIndexError, match="zero-norm"):
        ExactCosineIndex([make_chunk("zero", "zero")], embedder=embedder)


def test_checked_in_embedding_manifest_is_pinned() -> None:
    manifest = (
        Path(__file__).resolve().parents[2]
        / "datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"
    )

    spec = load_embedding_model_spec(manifest)

    assert spec.model_id == "BAAI/bge-small-en-v1.5"
    assert spec.revision == "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    assert spec.dimension == 384
    assert spec.max_sequence_length == 512
    assert spec.license_name == "MIT"
