import json
from pathlib import Path

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import Chunk, Document, SourceManifest
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonDocumentRepository


def test_ingestion_pipeline_writes_one_idempotent_corpus_snapshot(
    source_manifest: SourceManifest,
    source_path: Path,
    tmp_path: Path,
) -> None:
    repository = JsonDocumentRepository(tmp_path)
    service = IngestionService(
        fetcher=LocalFileSourceFetcher(source_path),
        parser=SphinxApiParser(),
        chunker=ApiReferenceChunker(),
        repository=repository,
    )

    first = service.run(source_manifest)
    first_snapshot = repository.snapshot_path.read_bytes()
    second = service.run(source_manifest)

    payload = json.loads(repository.snapshot_path.read_text(encoding="utf-8"))
    stored_document = Document.model_validate(payload["documents"][0])
    stored_chunks = [Chunk.model_validate(item) for item in payload["chunks"]]

    assert first.document.document_id == second.document.document_id
    assert repository.snapshot_path.read_bytes() == first_snapshot
    assert payload["schema_version"] == "1"
    assert len(payload["documents"]) == 1
    assert len(payload["chunks"]) == 5
    assert stored_document == first.document
    assert {chunk.chunk_id for chunk in stored_chunks} == {chunk.chunk_id for chunk in first.chunks}
    assert repository.load_documents() == (first.document,)
    assert {chunk.chunk_id for chunk in repository.load_chunks()} == {
        chunk.chunk_id for chunk in first.chunks
    }
