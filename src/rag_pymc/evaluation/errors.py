"""Evaluation-specific failures."""


class EvaluationError(Exception):
    """Base class for controlled evaluation failures."""


class EvaluationDatasetError(EvaluationError):
    """Raised when an evaluation dataset cannot be loaded or validated."""
