"""Application service for one-source ingestion runs."""

from dataclasses import dataclass

from rag_pymc.domain import Chunk, Document, SourceManifest
from rag_pymc.ingestion.errors import IngestionError
from rag_pymc.ingestion.interfaces import Chunker, DocumentParser, DocumentRepository, SourceFetcher


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Artifacts produced by a successful ingestion run."""

    document: Document
    chunks: tuple[Chunk, ...]


@dataclass(frozen=True, slots=True)
class IngestionService:
    """Coordinate acquisition, parsing, chunking, and persistence."""

    fetcher: SourceFetcher
    parser: DocumentParser
    chunker: Chunker
    repository: DocumentRepository

    def run(self, manifest: SourceManifest) -> IngestionResult:
        """Ingest one source artifact through all configured boundaries."""
        source = self.fetcher.fetch(manifest)
        parsed = self.parser.parse(source, manifest)
        chunks = tuple(self.chunker.chunk(parsed))
        if not chunks:
            msg = f"chunker returned no chunks for {manifest.source_id}"
            raise IngestionError(msg)
        self.repository.save(parsed.document, chunks)
        return IngestionResult(document=parsed.document, chunks=chunks)
