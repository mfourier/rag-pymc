"""Small project-owned interfaces for the ingestion pipeline."""

from collections.abc import Sequence
from typing import Protocol

from rag_pymc.domain import Chunk, Document, SourceManifest
from rag_pymc.parsing.models import ParsedApiDocument


class SourceFetcher(Protocol):
    """Load one source artifact and verify it against a manifest."""

    def fetch(self, manifest: SourceManifest) -> bytes:
        """Return verified source bytes."""


class DocumentParser(Protocol):
    """Transform source bytes into a normalized document."""

    def parse(self, source: bytes, manifest: SourceManifest) -> ParsedApiDocument:
        """Parse one source artifact."""


class Chunker(Protocol):
    """Create structure-aware retrieval units from a parsed document."""

    def chunk(self, parsed: ParsedApiDocument) -> list[Chunk]:
        """Create deterministic chunks."""


class DocumentRepository(Protocol):
    """Persist normalized documents and chunks."""

    def save(self, document: Document, chunks: Sequence[Chunk]) -> None:
        """Upsert one document and its chunks."""
