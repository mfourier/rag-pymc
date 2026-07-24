from pathlib import Path

import pytest
from pydantic import ValidationError

from rag_pymc.domain import Chunk, Document, SourceType
from rag_pymc.evaluation import (
    EvaluationDatasetError,
    Phase5AnnotationCorpusFreeze,
    build_phase5_annotation_corpus_freeze,
    hash_phase5_corpus,
    write_phase5_annotation_corpus_freeze,
)
from tests.factories import make_chunk as make_test_chunk
from tests.factories import make_document

LIMITATIONS = ("The synthetic corpus is intentionally narrow.",)


def make_chunk(
    chunk_id: str,
    document: Document,
    *,
    chunker_version: str | None = "api-reference-v1",
) -> Chunk:
    content = f"Evidence for {chunk_id}."
    return make_test_chunk(
        chunk_id,
        content,
        document=document,
        section="Overview",
        symbols=(f"pymc.{document.document_id}",),
        chunker_version=chunker_version,
    )


def build_report(
    documents: tuple[Document, ...],
    chunks: tuple[Chunk, ...],
) -> Phase5AnnotationCorpusFreeze:
    return build_phase5_annotation_corpus_freeze(
        documents,
        chunks,
        annotation_namespace="pymc-6.1.0-api-phase5-development-v1",
        corpus_path="datasets/processed/phase5-annotation-api-v1",
        library="pymc",
        library_version="6.1.0",
        source_types=(SourceType.API_REFERENCE,),
        limitations=LIMITATIONS,
    )


def test_annotation_corpus_freeze_is_deterministic_and_complete(tmp_path: Path) -> None:
    first_document = make_document("first")
    second_document = make_document("second")
    first_chunk = make_chunk("chunk_a", first_document)
    second_chunk = make_chunk("chunk_b", second_document)

    report = build_report(
        (second_document, first_document),
        (second_chunk, first_chunk),
    )
    repeated = build_report(
        (first_document, second_document),
        (first_chunk, second_chunk),
    )

    assert report == repeated
    assert report.corpus_sha256 == hash_phase5_corpus((first_chunk, second_chunk))
    assert report.document_count == 2
    assert report.chunk_count == 2
    assert report.source_types == (SourceType.API_REFERENCE,)
    assert report.parser_versions == ("sphinx-api-v1",)
    assert report.chunker_versions == ("api-reference-v1",)
    assert report.api_symbols == ("pymc.first", "pymc.second")
    assert tuple(document.document_id for document in report.documents) == ("first", "second")

    output_path = tmp_path / "freeze.json"
    write_phase5_annotation_corpus_freeze(report, output_path)
    restored = Phase5AnnotationCorpusFreeze.model_validate_json(output_path.read_text())
    assert restored == report
    assert output_path.read_bytes().endswith(b"\n")


def test_annotation_corpus_freeze_rejects_an_undeclared_source_layer() -> None:
    document = make_document("guide", source_type=SourceType.CONCEPTUAL_GUIDE)
    chunk = make_chunk("chunk_a", document)

    with pytest.raises(EvaluationDatasetError, match="source types do not match"):
        build_report((document,), (chunk,))


def test_annotation_corpus_freeze_rejects_a_chunk_without_its_parent() -> None:
    document = make_document("included")
    other_document = make_document("missing")
    chunk = make_chunk("chunk_a", other_document)

    with pytest.raises(EvaluationDatasetError, match="references a missing document"):
        build_report((document,), (chunk,))


@pytest.mark.parametrize(
    ("document", "chunk", "message"),
    [
        (make_document("document", parser_version=None), None, "require parser versions"),
        (
            make_document("document"),
            "missing-chunker-version",
            "require chunker versions",
        ),
    ],
)
def test_annotation_corpus_freeze_requires_transformation_versions(
    document: Document,
    chunk: str | None,
    message: str,
) -> None:
    resolved_chunk = make_chunk(
        "chunk_a",
        document,
        chunker_version=None if chunk else "api-reference-v1",
    )

    with pytest.raises(EvaluationDatasetError, match=message):
        build_report((document,), (resolved_chunk,))


def test_annotation_corpus_freeze_rejects_a_machine_specific_path() -> None:
    document = make_document("document")
    chunk = make_chunk("chunk_a", document)
    report = build_report((document,), (chunk,))

    with pytest.raises(ValidationError, match="project-relative"):
        Phase5AnnotationCorpusFreeze.model_validate(
            report.model_copy(update={"corpus_path": "/tmp/corpus"})
        )


def test_annotation_corpus_freeze_revalidates_document_aggregates() -> None:
    document = make_document("document")
    chunk = make_chunk("chunk_a", document)
    report = build_report((document,), (chunk,))

    with pytest.raises(ValidationError, match="parser_versions must match documents"):
        Phase5AnnotationCorpusFreeze.model_validate(
            report.model_copy(update={"parser_versions": ("changed-parser-v1",)})
        )
