from datetime import UTC, datetime
from hashlib import sha256

from rag_pymc.domain import Chunk, Difficulty, Document, SourceType

DEFAULT_CREATED_AT = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
DEFAULT_FETCHED_AT = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)


def make_document(
    document_id: str = "document_001",
    content: str | None = None,
    *,
    source_type: SourceType = SourceType.API_REFERENCE,
    parser_version: str | None = "sphinx-api-v1",
    **overrides: object,
) -> Document:
    resolved_content = content or f"Normalized content for {document_id}."
    values: dict[str, object] = {
        "document_id": document_id,
        "library": "pymc",
        "library_version": "6.1.0",
        "source_type": source_type,
        "source_url": f"https://docs.example.test/{document_id}.html",
        "title": document_id,
        "content": resolved_content,
        "content_hash": sha256(resolved_content.encode()).hexdigest(),
        "fetched_at": DEFAULT_FETCHED_AT,
        "source_commit": "a" * 40,
        "parser_version": parser_version,
    }
    values.update(overrides)
    return Document.model_validate(values)


def make_chunk(
    chunk_id: str = "chunk_001",
    content: str | None = None,
    *,
    library: str = "pymc",
    version: str = "6.1.0",
    source_type: SourceType = SourceType.API_REFERENCE,
    symbols: tuple[str, ...] = ("pymc.sample",),
    document: Document | None = None,
    **overrides: object,
) -> Chunk:
    resolved_content = content or f"content for {chunk_id}"
    values: dict[str, object] = {
        "chunk_id": chunk_id,
        "document_id": document.document_id if document else f"document_{chunk_id}",
        "library": document.library if document else library,
        "library_version": document.library_version if document else version,
        "source_type": document.source_type if document else source_type,
        "source_url": document.source_url if document else "https://example.test/source",
        "title": document.title if document else "Test source",
        "section": "Test",
        "content": resolved_content,
        "content_hash": sha256(resolved_content.encode()).hexdigest(),
        "api_symbols": symbols,
        "concepts": ("posterior_sampling",),
        "difficulty": Difficulty.INTERMEDIATE,
        "prerequisites": ("pymc.Model",),
        "contains_code": True,
        "created_at": document.fetched_at if document else DEFAULT_CREATED_AT,
    }
    values.update(overrides)
    return Chunk.model_validate(values)
