"""Sentence Transformers cross-encoder reranking adapter."""

from collections.abc import Sequence
from importlib.metadata import version

import numpy as np
import torch
from sentence_transformers import CrossEncoder

from rag_pymc.domain import Chunk
from rag_pymc.reranking.errors import (
    RerankingConfigurationError,
    RerankingInferenceError,
)
from rag_pymc.reranking.models import RerankingModelSpec


class SentenceTransformerCrossEncoderReranker:
    """Score technical query-chunk pairs with a pinned local cross-encoder."""

    name = "sentence-transformers-cross-encoder-v1"

    def __init__(
        self,
        spec: RerankingModelSpec,
        *,
        device: str = "cpu",
        batch_size: int = 16,
        seed: int = 20260720,
        local_files_only: bool = True,
    ) -> None:
        """Load and validate the configured cross-encoder."""
        if batch_size < 1:
            msg = "batch_size must be greater than zero"
            raise ValueError(msg)
        installed_version = version("sentence-transformers")
        if installed_version != spec.sentence_transformers_version:
            msg = (
                f"sentence-transformers {installed_version} does not match "
                f"manifest {spec.sentence_transformers_version}"
            )
            raise RerankingConfigurationError(msg)
        torch.manual_seed(seed)

        self.spec = spec
        self.model_id = spec.model_id
        self.revision = spec.revision
        self.device = device
        self.batch_size = batch_size
        self.seed = seed
        try:
            self._model = CrossEncoder(
                spec.model_id,
                revision=spec.revision,
                device=device,
                trust_remote_code=False,
                local_files_only=local_files_only,
                backend=spec.backend,
                max_length=spec.max_sequence_length,
            )
        except Exception as error:
            msg = f"unable to load reranking model {spec.model_id}@{spec.revision}"
            raise RerankingConfigurationError(msg) from error

        if self._model.max_seq_length != spec.max_sequence_length:
            msg = (
                f"model max sequence length {self._model.max_seq_length} "
                f"does not match manifest {spec.max_sequence_length}"
            )
            raise RerankingConfigurationError(msg)

    def score(self, query: str, chunks: Sequence[Chunk]) -> tuple[float, ...]:
        """Return raw relevance logits for query-chunk pairs."""
        if not chunks:
            return ()
        pairs = [(query, chunk.content) for chunk in chunks]
        try:
            values = self._model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
                apply_softmax=False,
                convert_to_numpy=True,
            )
        except Exception as error:
            msg = f"reranking inference failed for {self.model_id}"
            raise RerankingInferenceError(msg) from error

        scores = np.asarray(values, dtype=np.float64).reshape(-1)
        if scores.shape != (len(chunks),):
            msg = f"reranker score shape {scores.shape} does not match {(len(chunks),)}"
            raise RerankingInferenceError(msg)
        if not np.isfinite(scores).all():
            msg = "reranker scores contain non-finite values"
            raise RerankingInferenceError(msg)
        return tuple(float(score) for score in scores)

    def token_count(self, query: str, chunk: Chunk) -> int:
        """Count query-document word pieces without applying truncation."""
        token_ids = self._model.tokenizer.encode(
            query,
            chunk.content,
            add_special_tokens=True,
            truncation=False,
            verbose=False,
        )
        return len(token_ids)
