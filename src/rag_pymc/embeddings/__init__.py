"""Lightweight embedding contracts and provenance models."""

from rag_pymc.embeddings.errors import (
    EmbeddingConfigurationError,
    EmbeddingError,
    EmbeddingInferenceError,
)
from rag_pymc.embeddings.models import EmbeddingModelSpec, load_embedding_model_spec
from rag_pymc.embeddings.protocols import Embedder, EmbeddingMatrix

__all__ = [
    "Embedder",
    "EmbeddingConfigurationError",
    "EmbeddingError",
    "EmbeddingInferenceError",
    "EmbeddingMatrix",
    "EmbeddingModelSpec",
    "load_embedding_model_spec",
]
