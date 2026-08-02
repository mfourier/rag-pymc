"""Controlled API-corpus freezing and cross-version migration diagnostics."""

import os
import tempfile
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Literal, Self, cast

from pydantic import Field, model_validator

from rag_pymc.domain import Chunk, Document, SourceManifest
from rag_pymc.evaluation._model_base import EvaluationModel, NonEmptyString, Sha256
from rag_pymc.evaluation.dataset import load_evaluation_queries
from rag_pymc.evaluation.errors import EvaluationDatasetError
from rag_pymc.evaluation.retrieval_models import EvaluationQuery
from rag_pymc.serialization import canonical_json_bytes, canonical_json_sha256
from tools.development_dataset import hash_phase5_corpus
from tools.development_models import Phase5SingleReviewDataset

CORPUS_PROVENANCE_HASH_POLICY = "canonical-corpus-provenance-json-v2"


class ControlledApiSourceArtifact(EvaluationModel):
    """One exact fixture and manifest admitted to a controlled API corpus."""

    manifest_path: NonEmptyString
    fixture_path: NonEmptyString
    manifest: SourceManifest

    @model_validator(mode="after")
    def require_portable_paths(self) -> Self:
        """Reject absolute or traversing repository artifact paths."""
        for label, value in (
            ("manifest", self.manifest_path),
            ("fixture", self.fixture_path),
        ):
            path = PurePosixPath(value)
            if path.is_absolute() or ".." in path.parts:
                msg = f"controlled API {label} path must be project-relative without traversal"
                raise ValueError(msg)
        return self


class ControlledApiDocumentIdentity(EvaluationModel):
    """Normalized document identity retained by a controlled corpus freeze."""

    document_id: NonEmptyString
    title: NonEmptyString
    content_sha256: Sha256
    source_url: NonEmptyString
    source_commit: NonEmptyString
    parser_version: NonEmptyString


class ControlledApiChunkIdentity(EvaluationModel):
    """Normalized retrieval-unit identity retained by a controlled corpus freeze."""

    chunk_id: NonEmptyString
    document_id: NonEmptyString
    section: NonEmptyString
    content_sha256: Sha256
    api_symbols: tuple[NonEmptyString, ...] = Field(min_length=1)
    chunker_version: NonEmptyString


class ControlledApiCorpusFreeze(EvaluationModel):
    """Provenance-complete identity for one versioned API corpus."""

    schema_version: Literal["2"] = "2"
    freeze_version: Literal["controlled-api-corpus-freeze-v2"] = "controlled-api-corpus-freeze-v2"
    corpus_role: Literal["active-api-version-migration"] = "active-api-version-migration"
    corpus_id: NonEmptyString
    corpus_path: NonEmptyString
    corpus_hash_policy: Literal["canonical-corpus-provenance-json-v2"] = (
        "canonical-corpus-provenance-json-v2"
    )
    corpus_sha256: Sha256
    legacy_content_hash_policy: Literal["canonical-chunk-identity-json-v1"] = (
        "canonical-chunk-identity-json-v1"
    )
    legacy_content_sha256: Sha256
    library: NonEmptyString
    library_version: NonEmptyString
    release_tag: NonEmptyString
    source_commit: NonEmptyString
    sources: tuple[ControlledApiSourceArtifact, ...] = Field(min_length=1)
    documents: tuple[ControlledApiDocumentIdentity, ...] = Field(min_length=1)
    chunks: tuple[ControlledApiChunkIdentity, ...] = Field(min_length=1)
    document_count: int = Field(ge=1, strict=True)
    chunk_count: int = Field(ge=1, strict=True)
    parser_versions: tuple[NonEmptyString, ...] = Field(min_length=1)
    chunker_versions: tuple[NonEmptyString, ...] = Field(min_length=1)
    limitations: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_derived_identity(self) -> Self:
        """Require canonical components and a freshly derived provenance hash."""
        corpus_path = PurePosixPath(self.corpus_path)
        if corpus_path.is_absolute() or ".." in corpus_path.parts:
            raise ValueError("controlled API corpus path must be portable")
        identity_groups = (
            (tuple(item.manifest.source_id for item in self.sources), "sources"),
            (tuple(item.document_id for item in self.documents), "documents"),
            (tuple(item.chunk_id for item in self.chunks), "chunks"),
        )
        for identities, label in identity_groups:
            if identities != tuple(sorted(identities)) or len(set(identities)) != len(identities):
                msg = f"controlled API corpus {label} must be unique and ordered"
                raise ValueError(msg)
        if self.document_count != len(self.documents) or self.chunk_count != len(self.chunks):
            raise ValueError("controlled API corpus counts must match retained identities")
        if self.parser_versions != tuple(sorted(set(self.parser_versions))):
            raise ValueError("controlled API parser versions must be unique and ordered")
        if self.chunker_versions != tuple(sorted(set(self.chunker_versions))):
            raise ValueError("controlled API chunker versions must be unique and ordered")
        if self.limitations != tuple(sorted(set(self.limitations))):
            raise ValueError("controlled API limitations must be unique and ordered")
        if canonical_json_sha256(_freeze_hash_identity(self)) != self.corpus_sha256:
            raise ValueError("controlled API corpus provenance hash must match its components")
        return self


class RawFixtureMigration(EvaluationModel):
    """Raw-byte comparison for one API symbol across releases."""

    api_symbol: NonEmptyString
    from_sha256: Sha256
    to_sha256: Sha256
    exact_bytes: bool = Field(strict=True)


class PyMC620MigrationReport(EvaluationModel):
    """Mechanical 6.1.0-to-6.2.0 comparison that never claims human relabeling."""

    schema_version: Literal["1"] = "1"
    migration_version: Literal["pymc-6.2.0-controlled-migration-v1"] = (
        "pymc-6.2.0-controlled-migration-v1"
    )
    from_library_version: Literal["6.1.0"] = "6.1.0"
    from_corpus_hash_policy: Literal["canonical-chunk-identity-json-v1"] = (
        "canonical-chunk-identity-json-v1"
    )
    from_corpus_sha256: Sha256
    to_library_version: Literal["6.2.0"] = "6.2.0"
    to_corpus_hash_policy: Literal["canonical-corpus-provenance-json-v2"] = (
        "canonical-corpus-provenance-json-v2"
    )
    to_corpus_sha256: Sha256
    to_legacy_content_sha256: Sha256
    raw_fixtures: tuple[RawFixtureMigration, ...] = Field(min_length=1)
    normalized_document_count: int = Field(ge=1, strict=True)
    exact_normalized_document_count: int = Field(ge=0, strict=True)
    normalized_chunk_count: int = Field(ge=1, strict=True)
    exact_normalized_chunk_count: int = Field(ge=0, strict=True)
    reviewed_claim_count: int = Field(ge=0, strict=True)
    reviewed_support_set_count: int = Field(ge=0, strict=True)
    referenced_chunk_count: int = Field(ge=0, strict=True)
    exact_mapped_referenced_chunk_count: int = Field(ge=0, strict=True)
    exact_mapped_support_set_count: int = Field(ge=0, strict=True)
    human_review_migrated: Literal[False] = False
    independent_adjudication: Literal[False] = False
    held_out: Literal[False] = False
    threshold_selected: Literal[False] = False
    limitations: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_migration_counts(self) -> Self:
        """Keep exact-match counts bounded and comparison identities canonical."""
        symbols = tuple(item.api_symbol for item in self.raw_fixtures)
        if symbols != tuple(sorted(symbols)) or len(set(symbols)) != len(symbols):
            raise ValueError("migration raw fixtures must be unique and ordered")
        if self.exact_normalized_document_count > self.normalized_document_count:
            raise ValueError("exact document count cannot exceed compared documents")
        if self.exact_normalized_chunk_count > self.normalized_chunk_count:
            raise ValueError("exact chunk count cannot exceed compared chunks")
        if self.exact_mapped_referenced_chunk_count > self.referenced_chunk_count:
            raise ValueError("exact referenced-chunk mappings cannot exceed references")
        if self.exact_mapped_support_set_count > self.reviewed_support_set_count:
            raise ValueError("exact support-set mappings cannot exceed reviewed support sets")
        if self.limitations != tuple(sorted(set(self.limitations))):
            raise ValueError("migration limitations must be unique and ordered")
        return self


class RetrievalVersionProjectionReport(EvaluationModel):
    """Audit record for qrels projected only across exact normalized identities."""

    schema_version: Literal["1"] = "1"
    projection_version: Literal["pymc-6.2.0-exact-retrieval-projection-v1"] = (
        "pymc-6.2.0-exact-retrieval-projection-v1"
    )
    artifact_role: Literal["version-migration-retrieval-diagnostic"] = (
        "version-migration-retrieval-diagnostic"
    )
    from_library_version: Literal["6.1.0"] = "6.1.0"
    to_library_version: Literal["6.2.0"] = "6.2.0"
    source_dataset_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    source_dataset_sha256: Sha256
    projected_dataset_hash_policy: Literal["sha256-raw-file-bytes-v1"] = "sha256-raw-file-bytes-v1"
    projected_dataset_sha256: Sha256
    migration_report_sha256: Sha256
    target_corpus_sha256: Sha256
    query_count: int = Field(ge=1, strict=True)
    answerable_query_count: int = Field(ge=0, strict=True)
    referenced_document_count: int = Field(ge=0, strict=True)
    referenced_chunk_count: int = Field(ge=0, strict=True)
    projection_method: Literal["exact-normalized-document-and-chunk-identity"] = (
        "exact-normalized-document-and-chunk-identity"
    )
    new_human_judgment: Literal[False] = False
    held_out: Literal[False] = False
    threshold_selected: Literal[False] = False
    limitations: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_projection_counts(self) -> Self:
        """Keep the diagnostic boundary explicit and limitations canonical."""
        if self.answerable_query_count > self.query_count:
            raise ValueError("projection answerable count cannot exceed query count")
        if self.limitations != tuple(sorted(set(self.limitations))):
            raise ValueError("projection limitations must be unique and ordered")
        return self


def build_controlled_api_corpus_freeze(
    artifacts: Sequence[tuple[Path, Path]],
    documents: Sequence[Document],
    chunks: Sequence[Chunk],
    *,
    corpus_id: str,
    corpus_path: str,
    limitations: Sequence[str],
) -> ControlledApiCorpusFreeze:
    """Validate exact acquisition inputs and derive a provenance-complete corpus identity."""
    sources = tuple(sorted((_load_source_artifact(*pair) for pair in artifacts), key=_source_key))
    validated_documents = tuple(Document.model_validate(item) for item in documents)
    validated_chunks = tuple(Chunk.model_validate(item) for item in chunks)
    if not sources or not validated_documents or not validated_chunks:
        raise EvaluationDatasetError("controlled API freeze inputs must not be empty")
    boundaries = {
        (source.manifest.library.casefold(), source.manifest.library_version) for source in sources
    }
    if len(boundaries) != 1:
        raise EvaluationDatasetError("controlled API sources cross a library-version boundary")
    library, library_version = next(iter(boundaries))
    release_tags = {source.manifest.release_tag for source in sources}
    source_commits = {source.manifest.source_commit for source in sources}
    if None in release_tags or len(release_tags) != 1:
        raise EvaluationDatasetError("controlled API sources require one release tag")
    if None in source_commits or len(source_commits) != 1:
        raise EvaluationDatasetError("controlled API sources require one source commit")
    expected_by_symbol = {source.manifest.expected_api_symbol: source for source in sources}
    documents_by_title = {document.title: document for document in validated_documents}
    if set(documents_by_title) != set(expected_by_symbol):
        raise EvaluationDatasetError("controlled API documents must exactly cover source symbols")
    for title, document in documents_by_title.items():
        manifest = expected_by_symbol[title].manifest
        if (
            document.library.casefold() != library
            or document.library_version != library_version
            or str(document.source_url) != str(manifest.source_url)
            or document.source_commit != manifest.source_commit
        ):
            raise EvaluationDatasetError("controlled API document provenance mismatch")
    document_ids = {document.document_id for document in validated_documents}
    if any(
        chunk.document_id not in document_ids
        or chunk.library.casefold() != library
        or chunk.library_version != library_version
        for chunk in validated_chunks
    ):
        raise EvaluationDatasetError("controlled API chunks cross the document boundary")

    document_identities = tuple(
        sorted(
            (
                ControlledApiDocumentIdentity(
                    document_id=item.document_id,
                    title=item.title,
                    content_sha256=item.content_hash,
                    source_url=str(item.source_url),
                    source_commit=item.source_commit or "",
                    parser_version=item.parser_version or "",
                )
                for item in validated_documents
            ),
            key=lambda item: item.document_id,
        )
    )
    chunk_identities = tuple(
        sorted(
            (
                ControlledApiChunkIdentity(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    section=item.section or "",
                    content_sha256=item.content_hash,
                    api_symbols=item.api_symbols,
                    chunker_version=item.chunker_version or "",
                )
                for item in validated_chunks
            ),
            key=lambda item: item.chunk_id,
        )
    )
    library_value = next(iter({source.manifest.library for source in sources}))
    release_tag_value = cast(str, next(iter(release_tags)))
    source_commit_value = cast(str, next(iter(source_commits)))
    legacy_content_sha256 = hash_phase5_corpus(validated_chunks)
    parser_versions = tuple(sorted({item.parser_version for item in document_identities}))
    chunker_versions = tuple(sorted({item.chunker_version for item in chunk_identities}))
    canonical_limitations = tuple(sorted(set(limitations)))
    provisional = ControlledApiCorpusFreeze.model_construct(
        corpus_sha256="0" * 64,
        corpus_id=corpus_id,
        corpus_path=corpus_path,
        legacy_content_sha256=legacy_content_sha256,
        library=library_value,
        library_version=library_version,
        release_tag=release_tag_value,
        source_commit=source_commit_value,
        sources=sources,
        documents=document_identities,
        chunks=chunk_identities,
        document_count=len(document_identities),
        chunk_count=len(chunk_identities),
        parser_versions=parser_versions,
        chunker_versions=chunker_versions,
        limitations=canonical_limitations,
    )
    return ControlledApiCorpusFreeze(
        corpus_sha256=canonical_json_sha256(_freeze_hash_identity(provisional)),
        corpus_id=corpus_id,
        corpus_path=corpus_path,
        legacy_content_sha256=legacy_content_sha256,
        library=library_value,
        library_version=library_version,
        release_tag=release_tag_value,
        source_commit=source_commit_value,
        sources=sources,
        documents=document_identities,
        chunks=chunk_identities,
        document_count=len(document_identities),
        chunk_count=len(chunk_identities),
        parser_versions=parser_versions,
        chunker_versions=chunker_versions,
        limitations=canonical_limitations,
    )


def build_pymc_620_migration_report(
    old_artifacts: Sequence[tuple[Path, Path]],
    old_documents: Sequence[Document],
    old_chunks: Sequence[Chunk],
    new_freeze: ControlledApiCorpusFreeze,
    new_documents: Sequence[Document],
    new_chunks: Sequence[Chunk],
    reviewed_dataset: Phase5SingleReviewDataset,
) -> PyMC620MigrationReport:
    """Compare exact normalized evidence without creating new human labels."""
    reviewed_dataset = Phase5SingleReviewDataset.model_validate(reviewed_dataset)
    if hash_phase5_corpus(old_chunks) != reviewed_dataset.corpus_sha256:
        raise EvaluationDatasetError("migration source corpus does not match the reviewed dataset")
    if hash_phase5_corpus(new_chunks) != new_freeze.legacy_content_sha256:
        raise EvaluationDatasetError("migration target corpus does not match its freeze")
    old_sources = tuple(
        sorted((_load_source_artifact(*pair) for pair in old_artifacts), key=_source_key)
    )
    old_documents_by_title = {item.title: item for item in old_documents}
    new_documents_by_title = {item.title: item for item in new_documents}
    old_chunks_by_id = {item.chunk_id: item for item in old_chunks}
    new_chunks_by_id = {item.chunk_id: item for item in new_chunks}
    old_source_by_symbol = {item.manifest.expected_api_symbol: item for item in old_sources}
    new_source_by_symbol = {item.manifest.expected_api_symbol: item for item in new_freeze.sources}
    frozen_document_ids = {
        (item.document_id, item.title, item.content_sha256, item.parser_version)
        for item in new_freeze.documents
    }
    observed_document_ids = {
        (item.document_id, item.title, item.content_hash, item.parser_version or "")
        for item in new_documents
    }
    frozen_chunk_ids = {
        (
            item.chunk_id,
            item.document_id,
            item.section,
            item.content_sha256,
            item.api_symbols,
            item.chunker_version,
        )
        for item in new_freeze.chunks
    }
    observed_chunk_ids = {
        (
            item.chunk_id,
            item.document_id,
            item.section or "",
            item.content_hash,
            item.api_symbols,
            item.chunker_version or "",
        )
        for item in new_chunks
    }
    if frozen_document_ids != observed_document_ids or frozen_chunk_ids != observed_chunk_ids:
        raise EvaluationDatasetError("migration target records do not match the frozen corpus")
    if set(old_source_by_symbol) != set(new_source_by_symbol):
        raise EvaluationDatasetError("migration sources do not cover the same API symbols")
    raw_fixtures = tuple(
        RawFixtureMigration(
            api_symbol=symbol,
            from_sha256=old_source_by_symbol[symbol].manifest.content_hash,
            to_sha256=new_source_by_symbol[symbol].manifest.content_hash,
            exact_bytes=(
                old_source_by_symbol[symbol].manifest.content_hash
                == new_source_by_symbol[symbol].manifest.content_hash
            ),
        )
        for symbol in sorted(old_source_by_symbol)
    )
    exact_documents = sum(
        title in new_documents_by_title
        and _document_content_identity(document)
        == _document_content_identity(new_documents_by_title[title])
        for title, document in old_documents_by_title.items()
    )
    exact_chunks = sum(
        chunk_id in new_chunks_by_id
        and _chunk_content_identity(chunk) == _chunk_content_identity(new_chunks_by_id[chunk_id])
        for chunk_id, chunk in old_chunks_by_id.items()
    )
    referenced_ids = {
        chunk_id
        for example in reviewed_dataset.examples
        for claim in example.gold_claims
        for support_set in claim.support_sets
        for chunk_id in support_set.chunk_ids
    }
    mapped_references = {
        chunk_id
        for chunk_id in referenced_ids
        if chunk_id in old_chunks_by_id
        and chunk_id in new_chunks_by_id
        and _chunk_content_identity(old_chunks_by_id[chunk_id])
        == _chunk_content_identity(new_chunks_by_id[chunk_id])
    }
    support_sets = tuple(
        support_set
        for example in reviewed_dataset.examples
        for claim in example.gold_claims
        for support_set in claim.support_sets
    )
    exact_mapped_support_sets = sum(
        set(item.chunk_ids).issubset(mapped_references) for item in support_sets
    )
    return PyMC620MigrationReport(
        from_corpus_sha256=hash_phase5_corpus(old_chunks),
        to_corpus_sha256=new_freeze.corpus_sha256,
        to_legacy_content_sha256=new_freeze.legacy_content_sha256,
        raw_fixtures=raw_fixtures,
        normalized_document_count=len(old_documents_by_title),
        exact_normalized_document_count=exact_documents,
        normalized_chunk_count=len(old_chunks_by_id),
        exact_normalized_chunk_count=exact_chunks,
        reviewed_claim_count=sum(len(item.gold_claims) for item in reviewed_dataset.examples),
        reviewed_support_set_count=len(support_sets),
        referenced_chunk_count=len(referenced_ids),
        exact_mapped_referenced_chunk_count=len(mapped_references),
        exact_mapped_support_set_count=exact_mapped_support_sets,
        limitations=tuple(
            sorted(
                (
                    "Exact normalized text mapping is mechanical evidence and is not a new "
                    "human review decision for PyMC 6.2.0.",
                    "The source slice contains only four API pages and is not representative of "
                    "the complete PyMC documentation.",
                    "This migration diagnostic is exploratory, not held out, and selects no "
                    "evidence-sufficiency threshold.",
                )
            )
        ),
    )


def build_pymc_620_retrieval_projection(
    source_dataset_path: Path,
    migration_report_path: Path,
    target_freeze: ControlledApiCorpusFreeze,
) -> tuple[bytes, RetrievalVersionProjectionReport]:
    """Project retrieval qrels only when every normalized target identity is exact."""
    try:
        source_bytes = source_dataset_path.read_bytes()
        migration_bytes = migration_report_path.read_bytes()
        migration = PyMC620MigrationReport.model_validate_json(migration_bytes)
    except OSError as error:
        raise EvaluationDatasetError("unable to read retrieval projection inputs") from error
    if (
        migration.exact_normalized_document_count != migration.normalized_document_count
        or migration.exact_normalized_chunk_count != migration.normalized_chunk_count
        or migration.to_corpus_sha256 != target_freeze.corpus_sha256
    ):
        raise EvaluationDatasetError(
            "retrieval qrels require exact normalized migration identities"
        )
    queries = load_evaluation_queries(source_dataset_path)
    target_document_ids = {item.document_id for item in target_freeze.documents}
    target_chunk_ids = {item.chunk_id for item in target_freeze.chunks}
    projected: list[EvaluationQuery] = []
    for query in queries:
        if query.library is None:
            raise EvaluationDatasetError("retrieval projection queries require library routing")
        if query.library.casefold() != "pymc":
            if query.answerable:
                raise EvaluationDatasetError(
                    "retrieval projection cannot preserve answerable non-PyMC queries"
                )
            projected.append(query)
            continue
        if query.library_version != "6.1.0":
            raise EvaluationDatasetError("projected PyMC queries must originate from 6.1.0")
        if not set(query.relevant_document_ids).issubset(target_document_ids):
            raise EvaluationDatasetError(
                "retrieval projection references a missing target document"
            )
        if not set(query.relevant_chunk_ids).issubset(target_chunk_ids):
            raise EvaluationDatasetError("retrieval projection references a missing target chunk")
        projected.append(query.model_copy(update={"library_version": "6.2.0"}))
    projected_bytes = b"".join(
        canonical_json_bytes(query.model_dump(mode="json")) + b"\n" for query in projected
    )
    document_ids = {
        document_id for query in projected for document_id in query.relevant_document_ids
    }
    chunk_ids = {chunk_id for query in projected for chunk_id in query.relevant_chunk_ids}
    report = RetrievalVersionProjectionReport(
        source_dataset_sha256=sha256(source_bytes).hexdigest(),
        projected_dataset_sha256=sha256(projected_bytes).hexdigest(),
        migration_report_sha256=sha256(migration_bytes).hexdigest(),
        target_corpus_sha256=target_freeze.corpus_sha256,
        query_count=len(projected),
        answerable_query_count=sum(query.answerable for query in projected),
        referenced_document_count=len(document_ids),
        referenced_chunk_count=len(chunk_ids),
        limitations=tuple(
            sorted(
                (
                    "The projection changes only library_version after exact normalized identity "
                    "validation; it creates no new human judgment.",
                    "The source queries are development diagnostics, not a held-out evaluation "
                    "set for PyMC 6.2.0.",
                    "The projected dataset cannot support sufficiency calibration or production "
                    "quality claims.",
                )
            )
        ),
    )
    return projected_bytes, report


def write_bytes_atomically(content: bytes, path: Path, *, label: str) -> None:
    """Atomically write one deterministic generated byte artifact."""
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as output:
            output.write(content)
        os.replace(temporary_path, path)
    except OSError as error:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise EvaluationDatasetError(f"unable to write {label}: {path}") from error


def write_evaluation_model(report: EvaluationModel, path: Path) -> None:
    """Atomically write one validated evaluation model as indented JSON."""
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            text=True,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(report.model_dump_json(indent=2))
            output.write("\n")
        os.replace(temporary_path, path)
    except OSError as error:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise EvaluationDatasetError(f"unable to write controlled corpus report: {path}") from error


def _load_source_artifact(manifest_path: Path, fixture_path: Path) -> ControlledApiSourceArtifact:
    try:
        manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        fixture_hash = sha256(fixture_path.read_bytes()).hexdigest()
    except OSError as error:
        raise EvaluationDatasetError("unable to read controlled API source artifact") from error
    if fixture_hash != manifest.content_hash:
        raise EvaluationDatasetError(f"fixture SHA-256 does not match manifest: {fixture_path}")
    return ControlledApiSourceArtifact(
        manifest_path=manifest_path.as_posix(),
        fixture_path=fixture_path.as_posix(),
        manifest=manifest,
    )


def _freeze_hash_identity(freeze: ControlledApiCorpusFreeze) -> dict[str, object]:
    return {
        "hash_policy": CORPUS_PROVENANCE_HASH_POLICY,
        "corpus_id": freeze.corpus_id,
        "library": freeze.library,
        "library_version": freeze.library_version,
        "release_tag": freeze.release_tag,
        "source_commit": freeze.source_commit,
        "sources": [item.model_dump(mode="json") for item in freeze.sources],
        "documents": [item.model_dump(mode="json") for item in freeze.documents],
        "chunks": [item.model_dump(mode="json") for item in freeze.chunks],
    }


def _source_key(item: ControlledApiSourceArtifact) -> str:
    return item.manifest.source_id


def _document_content_identity(document: Document) -> tuple[str, str, str, str]:
    return (
        document.document_id,
        document.title,
        document.content_hash,
        document.parser_version or "",
    )


def _chunk_content_identity(chunk: Chunk) -> tuple[object, ...]:
    return (
        chunk.chunk_id,
        chunk.document_id,
        chunk.section,
        chunk.content_hash,
        chunk.api_symbols,
        chunk.chunker_version,
    )
