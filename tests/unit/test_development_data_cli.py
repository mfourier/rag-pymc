from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from rag_pymc.cli import app
from rag_pymc.domain import Chunk, Difficulty
from rag_pymc.evaluation import (
    AdjudicationProvenance,
    AnnotationProvenance,
    AtomicGoldClaim,
    GoldEvidenceSupportSet,
    Phase5DevelopmentCorpusValidation,
    Phase5DevelopmentExample,
    hash_phase5_corpus,
)
from rag_pymc.persistence import JsonlDocumentRepository

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
runner = CliRunner()


def write_development_example(
    path: Path,
    chunks: tuple[Chunk, ...],
    *,
    corpus_sha256: str | None = None,
) -> None:
    support_chunk = chunks[0]
    example = Phase5DevelopmentExample(
        query_id="dev_q_001",
        query_text="What does pymc.sample do?",
        query_family="sampling-api",
        template_family="single-api-overview",
        library="pymc",
        library_version="6.1.0",
        corpus_hash_policy="canonical-chunk-identity-json-v1",
        corpus_sha256=corpus_sha256 or hash_phase5_corpus(chunks),
        corpus_answerable=True,
        intent="sampling",
        difficulty=Difficulty.BEGINNER,
        expected_api_symbols=("pymc.sample",),
        gold_claims=(
            AtomicGoldClaim(
                claim_id="dev_q_001_claim_001",
                text="pymc.sample draws posterior samples.",
                support_sets=(GoldEvidenceSupportSet(chunk_ids=(support_chunk.chunk_id,)),),
            ),
        ),
        annotation=AnnotationProvenance(
            annotator_ids=("annotator_001",),
            guideline_version="phase5-annotation-guidelines-v1",
            batch_id="annotation-batch-001",
            annotated_at=NOW,
        ),
        adjudication=AdjudicationProvenance(
            adjudicator_ids=("adjudicator_001",),
            guideline_version="phase5-adjudication-guidelines-v1",
            batch_id="adjudication-batch-001",
            adjudicated_at=NOW,
        ),
    )
    path.write_text(f"{example.model_dump_json()}\n", encoding="utf-8")


def build_corpus(
    manifest_path: Path,
    source_path: Path,
    output_dir: Path,
) -> tuple[Chunk, ...]:
    result = runner.invoke(
        app,
        [
            "ingest",
            "--manifest",
            str(manifest_path),
            "--source",
            str(source_path),
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0
    return JsonlDocumentRepository(output_dir).load_chunks()


def test_validate_development_data_emits_only_the_canonical_audit_json(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
) -> None:
    corpus_dir = tmp_path / "corpus"
    dataset_path = tmp_path / "development.jsonl"
    chunks = build_corpus(manifest_path, source_path, corpus_dir)
    write_development_example(dataset_path, chunks)

    first = runner.invoke(
        app,
        [
            "validate-development-data",
            "--dataset",
            str(dataset_path),
            "--corpus-dir",
            str(corpus_dir),
        ],
    )
    second = runner.invoke(
        app,
        [
            "validate-development-data",
            "--dataset",
            str(dataset_path),
            "--corpus-dir",
            str(corpus_dir),
        ],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.stderr == ""
    assert first.stdout == second.stdout
    report = Phase5DevelopmentCorpusValidation.model_validate_json(first.stdout)
    assert report.corpus_sha256 == hash_phase5_corpus(chunks)
    assert report.corpus_chunk_count == len(chunks)
    assert report.query_count == 1
    assert report.gold_claim_count == 1
    assert report.referenced_chunk_ids == (chunks[0].chunk_id,)


def test_validate_development_data_fails_without_partial_json_on_hash_mismatch(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
) -> None:
    corpus_dir = tmp_path / "corpus"
    dataset_path = tmp_path / "development.jsonl"
    chunks = build_corpus(manifest_path, source_path, corpus_dir)
    write_development_example(dataset_path, chunks, corpus_sha256="d" * 64)

    result = runner.invoke(
        app,
        [
            "validate-development-data",
            "--dataset",
            str(dataset_path),
            "--corpus-dir",
            str(corpus_dir),
        ],
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "development-data validation failed:" in result.stderr
    assert "SHA-256 mismatch" in result.stderr
