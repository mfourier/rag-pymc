from pathlib import Path

import numpy as np
import pytest

from rag_pymc.embeddings import load_embedding_model_spec
from rag_pymc.embeddings.errors import EmbeddingConfigurationError
from rag_pymc.embeddings.sentence_transformer import SentenceTransformerEmbedder


class FakeTokenizer:
    def encode(self, text: str, **kwargs: object) -> list[int]:
        return list(range(len(text.split()) + 2))


class FakeSentenceTransformer:
    last_instance: "FakeSentenceTransformer | None" = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs
        self.max_seq_length = 512
        self.tokenizer = FakeTokenizer()
        self.document_inputs: list[str] = []
        self.query_inputs: list[str] = []
        FakeSentenceTransformer.last_instance = self

    def get_embedding_dimension(self) -> int:
        return 384

    def encode_document(self, texts: list[str], **kwargs: object) -> np.ndarray:
        self.document_inputs = texts
        return np.ones((len(texts), 384), dtype=np.float32)

    def encode_query(self, texts: list[str], **kwargs: object) -> np.ndarray:
        self.query_inputs = texts
        return np.ones((len(texts), 384), dtype=np.float32)


def test_sentence_transformer_adapter_uses_pinned_revision_and_query_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = (
        Path(__file__).resolve().parents[2]
        / "datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"
    )
    spec = load_embedding_model_spec(manifest)
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.SentenceTransformer",
        FakeSentenceTransformer,
    )
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.version",
        lambda _: "5.6.0",
    )

    embedder = SentenceTransformerEmbedder(spec, seed=7, local_files_only=True)
    document_matrix = embedder.embed_documents(["Document"])
    query_matrix = embedder.embed_query("What is observed?")
    model = FakeSentenceTransformer.last_instance

    assert model is not None
    assert model.args == (spec.model_id,)
    assert model.kwargs["revision"] == spec.revision
    assert model.kwargs["local_files_only"] is True
    assert model.document_inputs == ["Document"]
    assert model.query_inputs == [
        "Represent this sentence for searching relevant passages: What is observed?"
    ]
    assert document_matrix.shape == (1, 384)
    assert query_matrix.shape == (1, 384)
    assert embedder.token_count("two tokens") == 4


def test_sentence_transformer_adapter_rejects_package_version_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = (
        Path(__file__).resolve().parents[2]
        / "datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"
    )
    spec = load_embedding_model_spec(manifest)
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.version",
        lambda _: "5.5.0",
    )

    with pytest.raises(EmbeddingConfigurationError, match="does not match manifest"):
        SentenceTransformerEmbedder(spec)
