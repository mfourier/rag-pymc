"""Deterministic local JSON Lines persistence for corpus baselines."""

import os
import tempfile
from collections.abc import Iterable, Sequence
from pathlib import Path

from pydantic import ValidationError

from rag_pymc.domain import Chunk, Document
from rag_pymc.ingestion.errors import CorpusPersistenceError


class JsonlDocumentRepository:
    """Upsert documents and chunks into deterministic JSONL snapshots."""

    def __init__(self, output_dir: Path) -> None:
        """Configure the corpus directory and its two JSONL files."""
        self.output_dir = output_dir
        self.documents_path = output_dir / "documents.jsonl"
        self.chunks_path = output_dir / "chunks.jsonl"

    def save(self, document: Document, chunks: Sequence[Chunk]) -> None:
        """Upsert one document and replace all chunks belonging to it."""
        invalid_chunk = next(
            (chunk for chunk in chunks if chunk.document_id != document.document_id),
            None,
        )
        if invalid_chunk is not None:
            msg = (
                f"chunk {invalid_chunk.chunk_id} references {invalid_chunk.document_id}, "
                f"expected {document.document_id}"
            )
            raise CorpusPersistenceError(msg)

        documents = self._read_documents()
        documents[document.document_id] = document

        stored_chunks = {
            chunk_id: chunk
            for chunk_id, chunk in self._read_chunks().items()
            if chunk.document_id != document.document_id
        }
        stored_chunks.update({chunk.chunk_id: chunk for chunk in chunks})

        self._atomic_write(
            self.documents_path,
            (documents[key] for key in sorted(documents)),
        )
        self._atomic_write(
            self.chunks_path,
            (stored_chunks[key] for key in sorted(stored_chunks)),
        )

    def load_documents(self) -> tuple[Document, ...]:
        """Load validated documents in deterministic ID order."""
        documents = self._read_documents()
        return tuple(documents[key] for key in sorted(documents))

    def load_chunks(self) -> tuple[Chunk, ...]:
        """Load validated chunks in deterministic ID order."""
        chunks = self._read_chunks()
        return tuple(chunks[key] for key in sorted(chunks))

    def _read_documents(self) -> dict[str, Document]:
        documents: dict[str, Document] = {}
        for line_number, line in self._read_lines(self.documents_path):
            try:
                document = Document.model_validate_json(line)
            except ValidationError as error:
                msg = f"invalid document at {self.documents_path}:{line_number}"
                raise CorpusPersistenceError(msg) from error
            documents[document.document_id] = document
        return documents

    def _read_chunks(self) -> dict[str, Chunk]:
        chunks: dict[str, Chunk] = {}
        for line_number, line in self._read_lines(self.chunks_path):
            try:
                chunk = Chunk.model_validate_json(line)
            except ValidationError as error:
                msg = f"invalid chunk at {self.chunks_path}:{line_number}"
                raise CorpusPersistenceError(msg) from error
            chunks[chunk.chunk_id] = chunk
        return chunks

    @staticmethod
    def _read_lines(path: Path) -> list[tuple[int, str]]:
        if not path.exists():
            return []
        try:
            return [
                (line_number, line)
                for line_number, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(),
                    start=1,
                )
                if line.strip()
            ]
        except OSError as error:
            msg = f"unable to read corpus file: {path}"
            raise CorpusPersistenceError(msg) from error

    def _atomic_write(self, path: Path, records: Iterable[Document | Chunk]) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.output_dir,
                prefix=f".{path.name}.",
                text=True,
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                for record in records:
                    output.write(record.model_dump_json())
                    output.write("\n")
            os.replace(temporary_path, path)
        except OSError as error:
            if "temporary_path" in locals():
                temporary_path.unlink(missing_ok=True)
            msg = f"unable to write corpus file: {path}"
            raise CorpusPersistenceError(msg) from error
