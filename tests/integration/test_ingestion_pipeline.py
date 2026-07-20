from pathlib import Path

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import Chunk, Document, SourceManifest
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonlDocumentRepository


def test_ingestion_pipeline_writes_idempotent_jsonl_corpus(
    source_manifest: SourceManifest,
    source_path: Path,
    tmp_path: Path,
) -> None:
    repository = JsonlDocumentRepository(tmp_path)
    service = IngestionService(
        fetcher=LocalFileSourceFetcher(source_path),
        parser=SphinxApiParser(),
        chunker=ApiReferenceChunker(),
        repository=repository,
    )

    first = service.run(source_manifest)
    second = service.run(source_manifest)

    document_lines = repository.documents_path.read_text(encoding="utf-8").splitlines()
    chunk_lines = repository.chunks_path.read_text(encoding="utf-8").splitlines()
    stored_document = Document.model_validate_json(document_lines[0])
    stored_chunks = [Chunk.model_validate_json(line) for line in chunk_lines]

    assert first.document.document_id == second.document.document_id
    assert len(document_lines) == 1
    assert len(chunk_lines) == 5
    assert stored_document == first.document
    assert {chunk.chunk_id for chunk in stored_chunks} == {chunk.chunk_id for chunk in first.chunks}
    assert repository.load_documents() == (first.document,)
    assert {chunk.chunk_id for chunk in repository.load_chunks()} == {
        chunk.chunk_id for chunk in first.chunks
    }
