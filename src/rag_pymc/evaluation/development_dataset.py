"""Deterministic loading for Phase 5 corpus-level development annotations."""

import json
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rag_pymc.domain import Chunk, Document, SourceType
from rag_pymc.evaluation.errors import EvaluationDatasetError
from rag_pymc.evaluation.models import (
    Phase5AnnotationCorpusDocument,
    Phase5AnnotationCorpusFreeze,
    Phase5DevelopmentCorpusValidation,
    Phase5DevelopmentDataset,
    Phase5DevelopmentExample,
)


class _DuplicateJsonKeyError(ValueError):
    """Signal an ambiguous JSON object without retaining its controlled key."""


class _NonFiniteJsonNumberError(ValueError):
    """Signal a non-standard JSON numeric constant without retaining its value."""


def load_phase5_development_dataset(path: Path) -> Phase5DevelopmentDataset:
    """Load adjudicated development examples and hash the exact source-file bytes."""
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        msg = f"unable to read Phase 5 development dataset: {path}"
        raise EvaluationDatasetError(msg) from error

    dataset_sha256 = sha256(raw_bytes).hexdigest()
    try:
        text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        line_number = raw_bytes[: error.start].count(b"\n") + 1
        msg = f"invalid UTF-8 in Phase 5 development dataset at {path}:{line_number}"
        raise EvaluationDatasetError(msg) from error

    examples: list[Phase5DevelopmentExample] = []
    seen_query_ids: set[str] = set()
    seen_claim_ids: set[str] = set()
    corpus_sha256: str | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue

        try:
            raw_example = json.loads(
                line,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_non_finite_json_number,
            )
            example = Phase5DevelopmentExample.model_validate(raw_example)
        except (json.JSONDecodeError, RecursionError, ValidationError, ValueError) as error:
            msg = f"invalid Phase 5 development example at {path}:{line_number}"
            raise EvaluationDatasetError(msg) from error

        if example.query_id in seen_query_ids:
            msg = (
                f"duplicate Phase 5 development query_id at "
                f"{path}:{line_number}: {example.query_id}"
            )
            raise EvaluationDatasetError(msg)
        seen_query_ids.add(example.query_id)

        duplicate_claim_ids = tuple(
            claim.claim_id for claim in example.gold_claims if claim.claim_id in seen_claim_ids
        )
        if duplicate_claim_ids:
            msg = (
                f"duplicate Phase 5 development claim_id at "
                f"{path}:{line_number}: {duplicate_claim_ids[0]}"
            )
            raise EvaluationDatasetError(msg)
        seen_claim_ids.update(claim.claim_id for claim in example.gold_claims)

        if corpus_sha256 is None:
            corpus_sha256 = example.corpus_sha256
        elif example.corpus_sha256 != corpus_sha256:
            msg = f"inconsistent Phase 5 corpus_sha256 at {path}:{line_number}"
            raise EvaluationDatasetError(msg)

        examples.append(example)

    if not examples:
        msg = f"Phase 5 development dataset is empty: {path}"
        raise EvaluationDatasetError(msg)

    assert corpus_sha256 is not None
    return Phase5DevelopmentDataset(
        dataset_sha256=dataset_sha256,
        corpus_hash_policy="canonical-chunk-identity-json-v1",
        corpus_sha256=corpus_sha256,
        examples=tuple(examples),
    )


def hash_phase5_corpus(chunks: Sequence[Chunk]) -> str:
    """Hash canonical chunk identity and content hashes for Phase 5 annotations."""
    validated = tuple(Chunk.model_validate(chunk) for chunk in chunks)
    chunk_ids = tuple(chunk.chunk_id for chunk in validated)
    if len(set(chunk_ids)) != len(chunk_ids):
        msg = "cannot hash a Phase 5 corpus with duplicate chunk IDs"
        raise EvaluationDatasetError(msg)
    identity = tuple(
        {"chunk_id": chunk.chunk_id, "content_sha256": chunk.content_hash}
        for chunk in sorted(validated, key=lambda chunk: chunk.chunk_id)
    )
    canonical_json = json.dumps(
        identity,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_json.encode("ascii")).hexdigest()


def build_phase5_annotation_corpus_freeze(
    documents: Sequence[Document],
    chunks: Sequence[Chunk],
    *,
    annotation_namespace: str,
    corpus_path: str,
    library: str,
    library_version: str,
    source_types: Sequence[SourceType],
    limitations: Sequence[str],
) -> Phase5AnnotationCorpusFreeze:
    """Validate and describe the exact processed corpus used for Phase 5 annotation."""
    validated_documents = tuple(Document.model_validate(document) for document in documents)
    validated_chunks = tuple(Chunk.model_validate(chunk) for chunk in chunks)
    if not validated_documents:
        msg = "Phase 5 annotation corpus must contain at least one document"
        raise EvaluationDatasetError(msg)
    if not validated_chunks:
        msg = "Phase 5 annotation corpus must contain at least one chunk"
        raise EvaluationDatasetError(msg)

    document_ids = tuple(document.document_id for document in validated_documents)
    if len(set(document_ids)) != len(document_ids):
        msg = "Phase 5 annotation corpus contains duplicate document IDs"
        raise EvaluationDatasetError(msg)
    chunk_ids = tuple(chunk.chunk_id for chunk in validated_chunks)
    if len(set(chunk_ids)) != len(chunk_ids):
        msg = "Phase 5 annotation corpus contains duplicate chunk IDs"
        raise EvaluationDatasetError(msg)

    expected_source_types = tuple(source_types)
    if not expected_source_types:
        msg = "Phase 5 annotation corpus requires at least one expected source type"
        raise EvaluationDatasetError(msg)
    if len(set(expected_source_types)) != len(expected_source_types):
        msg = "Phase 5 annotation corpus expected source types must be unique"
        raise EvaluationDatasetError(msg)

    actual_source_types = tuple(
        sorted(
            {document.source_type for document in validated_documents}
            | {chunk.source_type for chunk in validated_chunks},
            key=lambda item: item.value,
        )
    )
    canonical_expected_source_types = tuple(
        sorted(expected_source_types, key=lambda item: item.value)
    )
    if actual_source_types != canonical_expected_source_types:
        msg = (
            "Phase 5 annotation corpus source types do not match the declared source types: "
            f"expected {[item.value for item in canonical_expected_source_types]}, "
            f"got {[item.value for item in actual_source_types]}"
        )
        raise EvaluationDatasetError(msg)

    normalized_library = library.casefold()
    document_outside_namespace = any(
        document.library.casefold() != normalized_library
        or document.library_version != library_version
        for document in validated_documents
    )
    chunk_outside_namespace = any(
        chunk.library.casefold() != normalized_library or chunk.library_version != library_version
        for chunk in validated_chunks
    )
    if document_outside_namespace or chunk_outside_namespace:
        msg = (
            "Phase 5 annotation corpus contains a record outside the declared "
            f"{library} {library_version} namespace"
        )
        raise EvaluationDatasetError(msg)

    documents_by_id = {document.document_id: document for document in validated_documents}
    chunk_parent_ids: set[str] = set()
    for chunk in validated_chunks:
        document = documents_by_id.get(chunk.document_id)
        if document is None:
            msg = f"Phase 5 annotation chunk {chunk.chunk_id} references a missing document"
            raise EvaluationDatasetError(msg)
        if (
            chunk.library.casefold() != document.library.casefold()
            or chunk.library_version != document.library_version
            or chunk.source_type != document.source_type
            or chunk.source_url != document.source_url
        ):
            msg = f"Phase 5 annotation chunk {chunk.chunk_id} conflicts with its parent document"
            raise EvaluationDatasetError(msg)
        chunk_parent_ids.add(chunk.document_id)

    document_id_set = set(document_ids)
    if chunk_parent_ids != document_id_set:
        empty_document_id = min(document_id_set - chunk_parent_ids)
        msg = f"Phase 5 annotation document {empty_document_id} has no chunks"
        raise EvaluationDatasetError(msg)

    if any(document.parser_version is None for document in validated_documents):
        msg = "Phase 5 annotation corpus documents require parser versions"
        raise EvaluationDatasetError(msg)
    if any(chunk.chunker_version is None for chunk in validated_chunks):
        msg = "Phase 5 annotation corpus chunks require chunker versions"
        raise EvaluationDatasetError(msg)

    parser_versions = tuple(
        sorted(
            {document.parser_version for document in validated_documents if document.parser_version}
        )
    )
    chunker_versions = tuple(
        sorted({chunk.chunker_version for chunk in validated_chunks if chunk.chunker_version})
    )
    api_symbols = tuple(
        sorted({symbol for chunk in validated_chunks for symbol in chunk.api_symbols})
    )
    document_records = tuple(
        Phase5AnnotationCorpusDocument(
            document_id=document.document_id,
            content_sha256=document.content_hash,
            source_url=document.source_url,
            source_type=document.source_type,
            parser_version=document.parser_version,
            source_commit=document.source_commit,
        )
        for document in sorted(validated_documents, key=lambda item: item.document_id)
        if document.parser_version is not None
    )
    return Phase5AnnotationCorpusFreeze(
        annotation_namespace=annotation_namespace,
        corpus_path=corpus_path,
        corpus_sha256=hash_phase5_corpus(validated_chunks),
        library=library,
        library_version=library_version,
        source_types=actual_source_types,
        parser_versions=parser_versions,
        chunker_versions=chunker_versions,
        api_symbols=api_symbols,
        documents=document_records,
        document_count=len(validated_documents),
        chunk_count=len(validated_chunks),
        limitations=tuple(sorted(limitations)),
    )


def write_phase5_annotation_corpus_freeze(
    report: Phase5AnnotationCorpusFreeze,
    path: Path,
) -> None:
    """Write one validated, deterministic annotation-corpus freeze artifact."""
    validated = Phase5AnnotationCorpusFreeze.model_validate(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{validated.model_dump_json(indent=2)}\n", encoding="utf-8")


def validate_phase5_development_corpus(
    dataset: Phase5DevelopmentDataset,
    chunks: Sequence[Chunk],
) -> Phase5DevelopmentCorpusValidation:
    """Verify the dataset hash binding and every gold reference against available chunks."""
    dataset = Phase5DevelopmentDataset.model_validate(dataset)
    validated_chunks = tuple(Chunk.model_validate(chunk) for chunk in chunks)
    if not validated_chunks:
        msg = "Phase 5 development corpus must contain at least one chunk"
        raise EvaluationDatasetError(msg)

    actual_corpus_sha256 = hash_phase5_corpus(validated_chunks)
    if actual_corpus_sha256 != dataset.corpus_sha256:
        msg = (
            "Phase 5 development corpus SHA-256 mismatch: "
            f"expected {dataset.corpus_sha256}, got {actual_corpus_sha256}"
        )
        raise EvaluationDatasetError(msg)

    chunks_by_id = {chunk.chunk_id: chunk for chunk in validated_chunks}
    referenced_chunk_ids: set[str] = set()
    gold_claim_count = 0
    gold_support_set_count = 0
    for example in dataset.examples:
        for claim in example.gold_claims:
            gold_claim_count += 1
            for support_set in claim.support_sets:
                gold_support_set_count += 1
                for chunk_id in support_set.chunk_ids:
                    chunk = chunks_by_id.get(chunk_id)
                    if chunk is None:
                        msg = (
                            f"Phase 5 gold claim {claim.claim_id} references missing "
                            f"chunk {chunk_id}"
                        )
                        raise EvaluationDatasetError(msg)
                    if (
                        chunk.library.casefold() != example.library.casefold()
                        or chunk.library_version != example.library_version
                    ):
                        msg = (
                            f"Phase 5 gold claim {claim.claim_id} references chunk {chunk_id} "
                            "from a different library or version"
                        )
                        raise EvaluationDatasetError(msg)
                    referenced_chunk_ids.add(chunk_id)

    ordered_references = tuple(sorted(referenced_chunk_ids))
    return Phase5DevelopmentCorpusValidation(
        dataset_sha256=dataset.dataset_sha256,
        corpus_hash_policy=dataset.corpus_hash_policy,
        corpus_sha256=actual_corpus_sha256,
        corpus_chunk_count=len(validated_chunks),
        query_count=len(dataset.examples),
        answerable_query_count=sum(example.corpus_answerable for example in dataset.examples),
        gold_claim_count=gold_claim_count,
        gold_support_set_count=gold_support_set_count,
        referenced_chunk_ids=ordered_references,
        referenced_chunk_count=len(ordered_references),
    )


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError
        result[key] = value
    return result


def _reject_non_finite_json_number(_: str) -> None:
    raise _NonFiniteJsonNumberError
