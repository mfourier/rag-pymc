"""Sentence Transformers embedding adapter."""

from collections.abc import Sequence
from importlib.metadata import version

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from rag_pymc.embeddings.errors import EmbeddingConfigurationError, EmbeddingInferenceError
from rag_pymc.embeddings.models import EmbeddingModelSpec
from rag_pymc.embeddings.protocols import EmbeddingMatrix


class SentenceTransformerEmbedder:
    """Encode asymmetric retrieval inputs with a pinned local model revision."""

    name = "sentence-transformer-v1"

    def __init__(
        self,
        spec: EmbeddingModelSpec,
        *,
        device: str = "cpu",
        batch_size: int = 16,
        seed: int = 20260719,
        local_files_only: bool = True,
    ) -> None:
        """Load and validate the configured Sentence Transformers model."""
        if batch_size < 1:
            msg = "batch_size must be greater than zero"
            raise ValueError(msg)
        installed_version = version("sentence-transformers")
        if installed_version != spec.sentence_transformers_version:
            msg = (
                f"sentence-transformers {installed_version} does not match "
                f"manifest {spec.sentence_transformers_version}"
            )
            raise EmbeddingConfigurationError(msg)
        torch.manual_seed(seed)

        self.spec = spec
        self.model_id = spec.model_id
        self.revision = spec.revision
        self.device = device
        self.batch_size = batch_size
        self.seed = seed
        try:
            self._model = SentenceTransformer(
                spec.model_id,
                revision=spec.revision,
                device=device,
                trust_remote_code=False,
                local_files_only=local_files_only,
            )
        except Exception as error:
            msg = f"unable to load embedding model {spec.model_id}@{spec.revision}"
            raise EmbeddingConfigurationError(msg) from error

        dimension = self._model.get_embedding_dimension()
        if dimension != spec.dimension:
            msg = f"embedding dimension {dimension} does not match manifest {spec.dimension}"
            raise EmbeddingConfigurationError(msg)
        if self._model.max_seq_length != spec.max_sequence_length:
            msg = (
                f"model max sequence length {self._model.max_seq_length} "
                f"does not match manifest {spec.max_sequence_length}"
            )
            raise EmbeddingConfigurationError(msg)
        self.dimension = spec.dimension

    def embed_documents(self, texts: Sequence[str]) -> EmbeddingMatrix:
        """Encode documents with the model's document task and normalized output."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        try:
            embeddings = self._model.encode_document(
                list(texts),
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=self.spec.normalize_embeddings,
            )
        except Exception as error:
            msg = f"document embedding failed for {self.model_id}"
            raise EmbeddingInferenceError(msg) from error
        return self._validate_matrix(embeddings, expected_rows=len(texts))

    def embed_query(self, text: str) -> EmbeddingMatrix:
        """Encode one query with the model's query task and normalized output."""
        try:
            query_text = (
                f"{self.spec.query_prefix.rstrip()} {text}" if self.spec.query_prefix else text
            )
            embeddings = self._model.encode_query(
                [query_text],
                batch_size=1,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=self.spec.normalize_embeddings,
            )
        except Exception as error:
            msg = f"query embedding failed for {self.model_id}"
            raise EmbeddingInferenceError(msg) from error
        return self._validate_matrix(embeddings, expected_rows=1)

    def token_count(self, text: str) -> int:
        """Count input word pieces without applying model truncation."""
        token_ids = self._model.tokenizer.encode(
            text,
            add_special_tokens=True,
            truncation=False,
            verbose=False,
        )
        return len(token_ids)

    def _validate_matrix(self, value: object, *, expected_rows: int) -> EmbeddingMatrix:
        matrix = np.asarray(value, dtype=np.float32)
        if matrix.shape != (expected_rows, self.dimension):
            msg = (
                f"embedding matrix has shape {matrix.shape}, "
                f"expected {(expected_rows, self.dimension)}"
            )
            raise EmbeddingInferenceError(msg)
        if not np.isfinite(matrix).all():
            msg = "embedding matrix contains non-finite values"
            raise EmbeddingInferenceError(msg)
        return matrix
