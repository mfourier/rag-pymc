from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest
from pydantic import AnyUrl

from rag_pymc.domain import Chunk, SourceType
from rag_pymc.reranking import load_reranking_model_spec
from rag_pymc.reranking.errors import RerankingConfigurationError
from rag_pymc.reranking.sentence_transformer import (
    SentenceTransformerCrossEncoderReranker,
)


class FakeTokenizer:
    def encode(self, first: str, second: str, **kwargs: object) -> list[int]:
        return list(range(len(first.split()) + len(second.split()) + 3))


class FakeCrossEncoder:
    last_instance: "FakeCrossEncoder | None" = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs
        self.max_seq_length = 512
        self.tokenizer = FakeTokenizer()
        self.inputs: list[tuple[str, str]] = []
        FakeCrossEncoder.last_instance = self

    def predict(self, inputs: list[tuple[str, str]], **kwargs: object) -> np.ndarray:
        self.inputs = inputs
        return np.arange(len(inputs), dtype=np.float32)


def make_chunk(chunk_id: str) -> Chunk:
    content = f"technical content for {chunk_id}"
    return Chunk(
        chunk_id=chunk_id,
        document_id=f"doc_{chunk_id}",
        library="pymc",
        library_version="6.1.0",
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl("https://example.test/source"),
        title="Test source",
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        created_at=datetime(2026, 7, 20, tzinfo=UTC),
    )


def test_cross_encoder_adapter_uses_pinned_revision_and_raw_logits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = (
        Path(__file__).resolve().parents[2]
        / "datasets/raw/manifests/rerankers/ms-marco-MiniLM-L6-v2.json"
    )
    spec = load_reranking_model_spec(manifest)
    monkeypatch.setattr(
        "rag_pymc.reranking.sentence_transformer.CrossEncoder",
        FakeCrossEncoder,
    )
    monkeypatch.setattr(
        "rag_pymc.reranking.sentence_transformer.version",
        lambda _: "5.6.0",
    )
    chunks = (make_chunk("a"), make_chunk("b"))

    reranker = SentenceTransformerCrossEncoderReranker(
        spec,
        seed=7,
        local_files_only=True,
    )
    scores = reranker.score("query text", chunks)
    model = FakeCrossEncoder.last_instance

    assert model is not None
    assert model.args == (spec.model_id,)
    assert model.kwargs["revision"] == spec.revision
    assert model.kwargs["local_files_only"] is True
    assert model.kwargs["trust_remote_code"] is False
    assert model.kwargs["backend"] == "torch"
    assert model.kwargs["max_length"] == 512
    assert model.inputs == [
        ("query text", chunks[0].content),
        ("query text", chunks[1].content),
    ]
    assert scores == (0.0, 1.0)
    assert reranker.token_count("two tokens", chunks[0]) == 9


def test_cross_encoder_adapter_rejects_package_version_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = (
        Path(__file__).resolve().parents[2]
        / "datasets/raw/manifests/rerankers/ms-marco-MiniLM-L6-v2.json"
    )
    spec = load_reranking_model_spec(manifest)
    monkeypatch.setattr(
        "rag_pymc.reranking.sentence_transformer.version",
        lambda _: "5.5.0",
    )

    with pytest.raises(RerankingConfigurationError, match="does not match manifest"):
        SentenceTransformerCrossEncoderReranker(spec)
