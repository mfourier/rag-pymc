"""Atomic local JSON persistence for one coherent corpus snapshot."""

import os
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from rag_pymc.domain import Chunk, Document
from rag_pymc.ingestion.errors import CorpusPersistenceError


class _CorpusSnapshot(BaseModel):
    """Validated on-disk representation of documents and their chunks."""

    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

    schema_version: Literal["1"] = "1"
    documents: tuple[Document, ...] = ()
    chunks: tuple[Chunk, ...] = ()

    @model_validator(mode="after")
    def validate_identity_and_references(self) -> Self:
        """Require unique sorted identities and complete parent references."""
        document_ids = tuple(document.document_id for document in self.documents)
        chunk_ids = tuple(chunk.chunk_id for chunk in self.chunks)
        if len(set(document_ids)) != len(document_ids):
            raise ValueError("corpus snapshot contains duplicate document IDs")
        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("corpus snapshot contains duplicate chunk IDs")
        if document_ids != tuple(sorted(document_ids)):
            raise ValueError("corpus snapshot documents are not sorted by ID")
        if chunk_ids != tuple(sorted(chunk_ids)):
            raise ValueError("corpus snapshot chunks are not sorted by ID")
        missing_parent = next(
            (chunk for chunk in self.chunks if chunk.document_id not in set(document_ids)),
            None,
        )
        if missing_parent is not None:
            msg = f"chunk {missing_parent.chunk_id} references missing {missing_parent.document_id}"
            raise ValueError(msg)
        return self


class JsonDocumentRepository:
    """Upsert documents and chunks through one atomic corpus snapshot."""

    def __init__(self, output_dir: Path) -> None:
        """Configure the corpus directory and snapshot path."""
        self.output_dir = output_dir
        self.snapshot_path = output_dir / "corpus.json"

    def save(self, document: Document, chunks: Sequence[Chunk]) -> None:
        """Atomically upsert one document and replace all of its chunks."""
        chunk_ids = tuple(chunk.chunk_id for chunk in chunks)
        if len(set(chunk_ids)) != len(chunk_ids):
            raise CorpusPersistenceError("input contains duplicate chunk IDs")
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

        current = self._read_snapshot()
        documents = {item.document_id: item for item in current.documents}
        documents[document.document_id] = document
        stored_chunks = {
            chunk.chunk_id: chunk
            for chunk in current.chunks
            if chunk.document_id != document.document_id
        }
        stored_chunks.update({chunk.chunk_id: chunk for chunk in chunks})
        snapshot = _CorpusSnapshot(
            documents=tuple(documents[key] for key in sorted(documents)),
            chunks=tuple(stored_chunks[key] for key in sorted(stored_chunks)),
        )
        self._atomic_write(snapshot)

    def load_documents(self) -> tuple[Document, ...]:
        """Load validated documents in deterministic ID order."""
        return self._read_snapshot().documents

    def load_chunks(self) -> tuple[Chunk, ...]:
        """Load validated chunks in deterministic ID order."""
        return self._read_snapshot().chunks

    def _read_snapshot(self) -> _CorpusSnapshot:
        if not self.snapshot_path.exists():
            return _CorpusSnapshot()
        try:
            return _CorpusSnapshot.model_validate_json(
                self.snapshot_path.read_text(encoding="utf-8")
            )
        except ValidationError as error:
            msg = f"invalid corpus snapshot: {self.snapshot_path}"
            raise CorpusPersistenceError(msg) from error
        except OSError as error:
            msg = f"unable to read corpus snapshot: {self.snapshot_path}"
            raise CorpusPersistenceError(msg) from error

    def _atomic_write(self, snapshot: _CorpusSnapshot) -> None:
        temporary_path: Path | None = None
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.output_dir,
                prefix=f".{self.snapshot_path.name}.",
                text=True,
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(snapshot.model_dump_json())
                output.write("\n")
            os.replace(temporary_path, self.snapshot_path)
        except OSError as error:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            msg = f"unable to write corpus snapshot: {self.snapshot_path}"
            raise CorpusPersistenceError(msg) from error
