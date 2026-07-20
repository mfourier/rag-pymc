"""Reranking errors exposed at package boundaries."""


class RerankingError(Exception):
    """Base error for reranking failures."""


class RerankingConfigurationError(RerankingError, ValueError):
    """Raised when a reranker cannot be configured safely."""


class RerankingInferenceError(RerankingError):
    """Raised when a reranker returns invalid scores."""
