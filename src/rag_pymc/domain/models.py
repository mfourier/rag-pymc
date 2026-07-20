"""Validated domain models shared by ingestion and retrieval components."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    AnyUrl,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    StringConstraints,
    model_validator,
)

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class SourceType(StrEnum):
    """Supported source structures for parsing and chunking policies."""

    API_REFERENCE = "api_reference"
    CONCEPTUAL_GUIDE = "conceptual_guide"
    TUTORIAL = "tutorial"
    EXAMPLE = "example"
    NOTEBOOK = "notebook"
    REPOSITORY_CODE = "repository_code"
    PROJECT_NOTE = "project_note"
    TRACEBACK = "traceback"


class Difficulty(StrEnum):
    """Pedagogical difficulty assigned to a chunk when known."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DomainModel(BaseModel):
    """Strict and immutable base for values crossing component boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceManifest(DomainModel):
    """Provenance and integrity metadata for one acquired source artifact."""

    manifest_version: NonEmptyString = "1"
    source_id: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    source_type: SourceType
    source_url: AnyUrl
    release_tag: NonEmptyString | None = None
    release_url: AnyUrl | None = None
    source_commit: NonEmptyString | None = None
    source_last_modified_at: AwareDatetime | None = None
    downloaded_at: AwareDatetime
    content_hash: Sha256
    media_type: NonEmptyString
    expected_api_symbol: NonEmptyString | None = None
    license_name: NonEmptyString
    license_url: AnyUrl

    @model_validator(mode="after")
    def api_reference_requires_symbol(self) -> Self:
        """Require symbol identity for API reference sources."""
        if self.source_type is SourceType.API_REFERENCE and self.expected_api_symbol is None:
            msg = "expected_api_symbol is required for API reference sources"
            raise ValueError(msg)
        return self


class Document(DomainModel):
    """A normalized source document with reproducible provenance."""

    document_id: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    source_type: SourceType
    source_url: AnyUrl
    title: NonEmptyString
    content: NonEmptyString
    content_hash: Sha256
    language: NonEmptyString = "en"
    fetched_at: AwareDatetime
    source_commit: NonEmptyString | None = None
    license_name: NonEmptyString | None = None
    license_url: AnyUrl | None = None
    parser_version: NonEmptyString | None = None


class Chunk(DomainModel):
    """A structure-aware retrieval unit linked to its source document."""

    chunk_id: NonEmptyString
    document_id: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    source_type: SourceType
    source_url: AnyUrl
    title: NonEmptyString
    section: NonEmptyString | None = None
    content: NonEmptyString
    content_hash: Sha256
    api_symbols: tuple[NonEmptyString, ...] = ()
    concepts: tuple[NonEmptyString, ...] = ()
    difficulty: Difficulty | None = None
    prerequisites: tuple[NonEmptyString, ...] = ()
    contains_code: bool = False
    language: NonEmptyString = "en"
    created_at: AwareDatetime
    indexed_at: AwareDatetime | None = None
    chunker_version: NonEmptyString | None = None

    @model_validator(mode="after")
    def indexed_at_must_follow_creation(self) -> Self:
        """Reject chronologically inconsistent indexing metadata."""
        if self.indexed_at is not None and self.indexed_at < self.created_at:
            msg = "indexed_at must not be earlier than created_at"
            raise ValueError(msg)
        return self


class SearchQuery(DomainModel):
    """A retrieval request and its explicit metadata filters."""

    text: NonEmptyString
    top_k: int = Field(default=10, ge=1, le=100)
    library: NonEmptyString | None = None
    library_version: NonEmptyString | None = None
    source_types: tuple[SourceType, ...] = ()
    api_symbols: tuple[NonEmptyString, ...] = ()


class RetrievedChunk(DomainModel):
    """A ranked chunk returned by a named retrieval strategy."""

    chunk: Chunk
    score: FiniteFloat
    rank: int = Field(ge=1)
    retriever: NonEmptyString
