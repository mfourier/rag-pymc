"""Small project-owned interfaces for the ingestion pipeline."""

from collections.abc import Sequence
from typing import Protocol, TypeVar

from rag_pymc.domain import Chunk, Document, SourceManifest

ParsedDocumentT_co = TypeVar("ParsedDocumentT_co", covariant=True)
ParsedDocumentT_contra = TypeVar("ParsedDocumentT_contra", contravariant=True)


class ParsedDocument(Protocol):
    """Minimum parsed-document contract needed by ingestion orchestration."""

    @property
    def document(self) -> Document:
        """Return the normalized document shared by all parser outputs."""


class SourceFetcher(Protocol):
    """Load one source artifact and verify it against a manifest."""

    def fetch(self, manifest: SourceManifest) -> bytes:
        """Return verified source bytes."""


class DocumentParser(Protocol[ParsedDocumentT_co]):
    """Transform source bytes into a normalized document."""

    def parse(self, source: bytes, manifest: SourceManifest) -> ParsedDocumentT_co:
        """Parse one source artifact."""


class Chunker(Protocol[ParsedDocumentT_contra]):
    """Create structure-aware retrieval units from a parsed document."""

    def chunk(self, parsed: ParsedDocumentT_contra) -> list[Chunk]:
        """Create deterministic chunks."""


class DocumentRepository(Protocol):
    """Persist normalized documents and chunks."""

    def save(self, document: Document, chunks: Sequence[Chunk]) -> None:
        """Upsert one document and its chunks."""
