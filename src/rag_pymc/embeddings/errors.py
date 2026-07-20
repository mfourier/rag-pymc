"""Embedding configuration and inference failures."""


class EmbeddingError(Exception):
    """Base class for controlled embedding failures."""


class EmbeddingConfigurationError(EmbeddingError):
    """Raised when an embedding model specification is invalid or unavailable."""


class EmbeddingInferenceError(EmbeddingError):
    """Raised when a model cannot produce a valid embedding matrix."""
