"""Errors raised by source ingestion components."""


class IngestionError(Exception):
    """Base error for an ingestion run that cannot produce valid artifacts."""


class SourceIntegrityError(IngestionError):
    """Raised when a source artifact does not match its provenance manifest."""


class DocumentParseError(IngestionError):
    """Raised when source structure cannot satisfy the parser contract."""


class CorpusPersistenceError(IngestionError):
    """Raised when processed documents or chunks cannot be persisted safely."""
