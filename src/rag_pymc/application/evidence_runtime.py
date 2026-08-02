"""Composition and integrity checks for the authorized PyMC evidence runtime."""

from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Self
from urllib.parse import urlparse

from pydantic import Field, StringConstraints, ValidationError, model_validator

from rag_pymc.abstention import ConservativeAbstentionPolicy
from rag_pymc.application.evidence import (
    AuthorizedCorpusMetadata,
    Bm25Parameters,
    EvidenceInspectionService,
    EvidenceModel,
    EvidenceServiceError,
)
from rag_pymc.application.retrieval_runtime import build_sparse_runtime
from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import Chunk, Document, SourceManifest
from rag_pymc.ingestion.errors import CorpusPersistenceError
from rag_pymc.persistence import JsonDocumentRepository
from rag_pymc.serialization import canonical_json_sha256

DEFAULT_AUTHORIZED_CORPUS_DIR = Path("datasets/processed/pymc-6.2.0-api-v1")
DEFAULT_AUTHORIZED_CORPUS_FREEZE = Path("reports/evaluation/pymc-6.2.0-api-v1-freeze.json")
AUTHORIZED_CORPUS_ID = "pymc-6.2.0-api-v1"
AUTHORIZED_CORPUS_SHA256 = "796e7aee3f1fae1423bc04f0478381e6f7338afdd85d2f3a9d1d9cfa692c573a"
AUTHORIZED_LIBRARY_VERSION = "6.2.0"
AUTHORIZED_RELEASE_TAG = "v6.2.0"
OFFICIAL_PYMC_DOCS_HOST = "www.pymc.io"

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]

_SERVICE_LIMITATIONS = (
    "MCP exposes evidence but cannot guarantee that a host invokes these tools or uses their "
    "output in its final message.",
    "The conservative evidence policy does not currently authorize answer generation.",
    "This evidence-only service does not generate, validate, or endorse a natural-language answer.",
)


class AuthorizedCorpusLoadError(EvidenceServiceError):
    """Raised when local artifacts do not reproduce the authorized corpus."""


class _ControlledSourceArtifact(EvidenceModel):
    manifest_path: NonEmptyString
    fixture_path: NonEmptyString
    manifest: SourceManifest

    @model_validator(mode="after")
    def require_portable_paths(self) -> Self:
        for value in (self.manifest_path, self.fixture_path):
            path = PurePosixPath(value)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("controlled source paths must be project-relative")
        return self


class _ControlledDocumentIdentity(EvidenceModel):
    document_id: NonEmptyString
    title: NonEmptyString
    content_sha256: Sha256
    source_url: NonEmptyString
    source_commit: NonEmptyString
    parser_version: NonEmptyString


class _ControlledChunkIdentity(EvidenceModel):
    chunk_id: NonEmptyString
    document_id: NonEmptyString
    section: NonEmptyString
    content_sha256: Sha256
    api_symbols: tuple[NonEmptyString, ...] = Field(min_length=1)
    chunker_version: NonEmptyString


class _ControlledCorpusFreeze(EvidenceModel):
    schema_version: Literal["2"]
    freeze_version: Literal["controlled-api-corpus-freeze-v2"]
    corpus_role: NonEmptyString
    corpus_id: NonEmptyString
    corpus_path: NonEmptyString
    corpus_hash_policy: Literal["canonical-corpus-provenance-json-v2"]
    corpus_sha256: Sha256
    legacy_content_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    legacy_content_sha256: Sha256
    library: Literal["pymc"]
    library_version: Literal["6.2.0"]
    release_tag: Literal["v6.2.0"]
    source_commit: NonEmptyString
    sources: tuple[_ControlledSourceArtifact, ...] = Field(min_length=1)
    documents: tuple[_ControlledDocumentIdentity, ...] = Field(min_length=1)
    chunks: tuple[_ControlledChunkIdentity, ...] = Field(min_length=1)
    document_count: int = Field(ge=1, strict=True)
    chunk_count: int = Field(ge=1, strict=True)
    parser_versions: tuple[NonEmptyString, ...] = Field(min_length=1)
    chunker_versions: tuple[NonEmptyString, ...] = Field(min_length=1)
    limitations: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_provenance_hash(self) -> Self:
        groups = (
            tuple(item.manifest.source_id for item in self.sources),
            tuple(item.document_id for item in self.documents),
            tuple(item.chunk_id for item in self.chunks),
        )
        if any(group != tuple(sorted(set(group))) for group in groups):
            raise ValueError("controlled corpus identities must be unique and ordered")
        if self.document_count != len(self.documents) or self.chunk_count != len(self.chunks):
            raise ValueError("controlled corpus counts must match identities")
        if self.parser_versions != tuple(sorted(set(self.parser_versions))):
            raise ValueError("controlled corpus parser versions must be unique and ordered")
        if self.chunker_versions != tuple(sorted(set(self.chunker_versions))):
            raise ValueError("controlled corpus chunker versions must be unique and ordered")
        if self.limitations != tuple(sorted(set(self.limitations))):
            raise ValueError("controlled corpus limitations must be unique and ordered")
        expected = canonical_json_sha256(_freeze_hash_identity(self))
        if self.corpus_sha256 != expected:
            raise ValueError("controlled corpus provenance hash does not match its components")
        return self


def build_default_evidence_service(
    *,
    corpus_dir: Path = DEFAULT_AUTHORIZED_CORPUS_DIR,
    freeze_path: Path = DEFAULT_AUTHORIZED_CORPUS_FREEZE,
) -> EvidenceInspectionService:
    """Build the fixed local evidence runtime from repository-controlled artifacts."""
    freeze = _load_authorized_freeze(freeze_path)
    try:
        repository = JsonDocumentRepository(corpus_dir)
        documents = repository.load_documents()
        chunks = repository.load_chunks()
    except (CorpusPersistenceError, OSError, ValidationError, ValueError) as error:
        raise AuthorizedCorpusLoadError(
            "authorized PyMC corpus is unavailable or invalid"
        ) from error
    if not documents or not chunks:
        raise AuthorizedCorpusLoadError("authorized PyMC corpus is unavailable or empty")
    _validate_freeze_boundary(freeze, documents, chunks)

    runtime = build_sparse_runtime(chunks)
    metadata = AuthorizedCorpusMetadata(
        corpus_id=freeze.corpus_id,
        corpus_hash_policy=freeze.corpus_hash_policy,
        corpus_sha256=freeze.corpus_sha256,
        legacy_content_hash_policy=freeze.legacy_content_hash_policy,
        legacy_content_sha256=freeze.legacy_content_sha256,
        library=freeze.library,
        library_version=freeze.library_version,
        release_tag=freeze.release_tag,
        source_commit=freeze.source_commit,
        document_count=freeze.document_count,
        chunk_count=freeze.chunk_count,
        retriever="bm25-v1",
        tokenizer="technical-v1",
        bm25=Bm25Parameters(k1=runtime.index.k1, b=runtime.index.b),
        limitations=tuple(sorted(set((*freeze.limitations, *_SERVICE_LIMITATIONS)))),
    )
    return EvidenceInspectionService(
        documents=documents,
        chunks=chunks,
        corpus=metadata,
        retriever=runtime.retriever,
        context_builder=RankedContextBuilder(runtime.tokenizer),
        abstention_policy=ConservativeAbstentionPolicy(),
    )


def _load_authorized_freeze(path: Path) -> _ControlledCorpusFreeze:
    try:
        freeze = _ControlledCorpusFreeze.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as error:
        raise AuthorizedCorpusLoadError(
            "authorized PyMC corpus provenance is unavailable or invalid"
        ) from error
    if (
        freeze.corpus_id != AUTHORIZED_CORPUS_ID
        or freeze.corpus_sha256 != AUTHORIZED_CORPUS_SHA256
        or freeze.library_version != AUTHORIZED_LIBRARY_VERSION
        or freeze.release_tag != AUTHORIZED_RELEASE_TAG
    ):
        raise AuthorizedCorpusLoadError(
            "corpus provenance does not match the authorized PyMC release"
        )
    return freeze


def _validate_freeze_boundary(
    freeze: _ControlledCorpusFreeze,
    documents: tuple[Document, ...],
    chunks: tuple[Chunk, ...],
) -> None:
    frozen_documents = {
        (
            item.document_id,
            item.title,
            item.content_sha256,
            item.source_url,
            item.source_commit,
            item.parser_version,
        )
        for item in freeze.documents
    }
    observed_documents = {
        (
            item.document_id,
            item.title,
            item.content_hash,
            str(item.source_url),
            item.source_commit or "",
            item.parser_version or "",
        )
        for item in documents
    }
    frozen_chunks = {
        (
            item.chunk_id,
            item.document_id,
            item.section,
            item.content_sha256,
            item.api_symbols,
            item.chunker_version,
        )
        for item in freeze.chunks
    }
    observed_chunks = {
        (
            item.chunk_id,
            item.document_id,
            item.section or "",
            item.content_hash,
            item.api_symbols,
            item.chunker_version or "",
        )
        for item in chunks
    }
    legacy_identity = tuple(
        {"chunk_id": item.chunk_id, "content_sha256": item.content_hash}
        for item in sorted(chunks, key=lambda item: item.chunk_id)
    )
    if frozen_documents != observed_documents or frozen_chunks != observed_chunks:
        raise AuthorizedCorpusLoadError(
            "local PyMC corpus does not match the authorized provenance freeze"
        )
    if canonical_json_sha256(legacy_identity) != freeze.legacy_content_sha256:
        raise AuthorizedCorpusLoadError(
            "local PyMC corpus content hash does not match the authorized freeze"
        )
    for source in freeze.sources:
        manifest = source.manifest
        parsed = urlparse(str(manifest.source_url))
        if (
            parsed.scheme != "https"
            or parsed.hostname != OFFICIAL_PYMC_DOCS_HOST
            or not parsed.path.startswith("/projects/docs/")
            or manifest.library != freeze.library
            or manifest.library_version != freeze.library_version
            or manifest.release_tag != freeze.release_tag
            or manifest.source_commit != freeze.source_commit
            or manifest.license_name != "Apache-2.0"
        ):
            raise AuthorizedCorpusLoadError(
                "authorized PyMC source provenance is incomplete or non-official"
            )


def _freeze_hash_identity(freeze: _ControlledCorpusFreeze) -> dict[str, object]:
    return {
        "hash_policy": freeze.corpus_hash_policy,
        "corpus_id": freeze.corpus_id,
        "library": freeze.library,
        "library_version": freeze.library_version,
        "release_tag": freeze.release_tag,
        "source_commit": freeze.source_commit,
        "sources": [item.model_dump(mode="json") for item in freeze.sources],
        "documents": [item.model_dump(mode="json") for item in freeze.documents],
        "chunks": [item.model_dump(mode="json") for item in freeze.chunks],
    }
