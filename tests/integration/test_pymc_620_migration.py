"""Reproduce the controlled PyMC 6.2.0 corpus and version migration evidence."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from rag_pymc.application.retrieval_runtime import (
    build_sparse_experiment_config,
    build_sparse_runtime,
)
from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import SourceManifest
from rag_pymc.evaluation.dataset import load_evaluation_queries
from rag_pymc.evaluation.evaluator import RetrievalEvaluator
from rag_pymc.evaluation.retrieval_models import RetrievalExperimentReport
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonDocumentRepository
from tools.corpus_migration import (
    ControlledApiCorpusFreeze,
    PyMC620MigrationReport,
    RetrievalVersionProjectionReport,
    build_controlled_api_corpus_freeze,
    build_pymc_620_migration_report,
    build_pymc_620_retrieval_projection,
)
from tools.single_review import load_phase5_single_review_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAMES = (
    "pymc.Data",
    "pymc.model.core.set_data",
    "pymc.sample",
    "pymc.sample_posterior_predictive",
)
SOURCE_DATASET = Path("datasets/evaluation/phase4/pymc_core_queries.jsonl")
PROJECTED_DATASET = Path(
    "datasets/evaluation/migrations/pymc-6.2.0-phase4-exact-projection-v1.jsonl"
)
SINGLE_REVIEW_DATASET = Path("datasets/evaluation/phase5/development-single-review-v1.jsonl")
FREEZE_REPORT = Path("reports/evaluation/pymc-6.2.0-api-v1-freeze.json")
MIGRATION_REPORT = Path("reports/evaluation/pymc-6.1.0-to-6.2.0-migration-v1.json")
PROJECTION_REPORT = Path("reports/evaluation/pymc-6.2.0-phase4-exact-projection-v1.json")
RETRIEVAL_REPORT = Path("reports/evaluation/pymc-6.2.0-bm25-migration-v1.json")
LIMITATIONS = (
    "Chunk-identity equivalence does not establish semantic support, citation correctness, "
    "answer correctness, or usefulness.",
    "The corpus contains generated API reference pages for only four PyMC public symbols.",
    "The provenance-complete v2 hash is not comparable to the historical content-only v1 hash "
    "as though only content changed.",
)


def build_corpus(version: str, output_path: Path) -> JsonDocumentRepository:
    repository = JsonDocumentRepository(output_path)
    for source_name in SOURCE_NAMES:
        manifest_path = PROJECT_ROOT / f"datasets/raw/manifests/pymc/{version}/{source_name}.json"
        fixture_path = PROJECT_ROOT / f"datasets/fixtures/pymc/{version}/{source_name}.html"
        manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        IngestionService(
            fetcher=LocalFileSourceFetcher(fixture_path),
            parser=SphinxApiParser(),
            chunker=ApiReferenceChunker(),
            repository=repository,
        ).run(manifest)
    return repository


def source_artifacts(version: str) -> tuple[tuple[Path, Path], ...]:
    return tuple(
        (
            Path(f"datasets/raw/manifests/pymc/{version}/{name}.json"),
            Path(f"datasets/fixtures/pymc/{version}/{name}.html"),
        )
        for name in SOURCE_NAMES
    )


def test_pymc_620_migration_rebuilds_all_non_latency_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(PROJECT_ROOT)
    old_repository = build_corpus("6.1.0", tmp_path / "old-corpus")
    new_repository = build_corpus("6.2.0", tmp_path / "new-corpus")

    rebuilt_freeze = build_controlled_api_corpus_freeze(
        source_artifacts("6.2.0"),
        new_repository.load_documents(),
        new_repository.load_chunks(),
        corpus_id="pymc-6.2.0-api-v1",
        corpus_path="datasets/processed/pymc-6.2.0-api-v1",
        limitations=LIMITATIONS,
    )
    recorded_freeze = ControlledApiCorpusFreeze.model_validate_json(
        FREEZE_REPORT.read_text(encoding="utf-8")
    )
    assert rebuilt_freeze == recorded_freeze
    assert rebuilt_freeze.corpus_sha256 == (
        "796e7aee3f1fae1423bc04f0478381e6f7338afdd85d2f3a9d1d9cfa692c573a"
    )

    reviewed_dataset = load_phase5_single_review_dataset(SINGLE_REVIEW_DATASET)
    rebuilt_migration = build_pymc_620_migration_report(
        source_artifacts("6.1.0"),
        old_repository.load_documents(),
        old_repository.load_chunks(),
        rebuilt_freeze,
        new_repository.load_documents(),
        new_repository.load_chunks(),
        reviewed_dataset,
    )
    recorded_migration = PyMC620MigrationReport.model_validate_json(
        MIGRATION_REPORT.read_text(encoding="utf-8")
    )
    assert rebuilt_migration == recorded_migration
    assert rebuilt_migration.exact_normalized_document_count == 4
    assert rebuilt_migration.exact_normalized_chunk_count == 15
    assert rebuilt_migration.exact_mapped_support_set_count == 31
    assert rebuilt_migration.human_review_migrated is False

    projected_bytes, rebuilt_projection = build_pymc_620_retrieval_projection(
        SOURCE_DATASET,
        MIGRATION_REPORT,
        rebuilt_freeze,
    )
    recorded_projection = RetrievalVersionProjectionReport.model_validate_json(
        PROJECTION_REPORT.read_text(encoding="utf-8")
    )
    assert projected_bytes == PROJECTED_DATASET.read_bytes()
    assert rebuilt_projection == recorded_projection
    assert rebuilt_projection.new_human_judgment is False

    recorded_retrieval = RetrievalExperimentReport.model_validate_json(
        RETRIEVAL_REPORT.read_text(encoding="utf-8")
    )
    chunks = new_repository.load_chunks()
    runtime = build_sparse_runtime(
        chunks,
        k1=recorded_retrieval.config.k1,
        b=recorded_retrieval.config.b,
    )
    config = build_sparse_experiment_config(
        chunks,
        index=runtime.index,
        tokenizer=runtime.tokenizer,
        seed=recorded_retrieval.config.seed,
        top_k=recorded_retrieval.config.top_k,
    )
    rebuilt_retrieval = RetrievalEvaluator(
        retriever=runtime.retriever,
        chunks=chunks,
        tokenizer=runtime.tokenizer,
        config=config,
        experiment_id=recorded_retrieval.experiment_id,
        limitations=recorded_retrieval.limitations,
    ).evaluate(
        load_evaluation_queries(PROJECTED_DATASET),
        dataset_path=PROJECTED_DATASET,
        generated_at=datetime(2026, 8, 2, tzinfo=UTC),
    )
    assert _without_machine_specific_fields(rebuilt_retrieval) == (
        _without_machine_specific_fields(recorded_retrieval)
    )


def test_pymc_620_freeze_rejects_release_identity_tampering() -> None:
    payload = json.loads(FREEZE_REPORT.read_text(encoding="utf-8"))
    payload["library_version"] = "6.2.1"

    with pytest.raises(ValidationError, match="provenance hash must match"):
        ControlledApiCorpusFreeze.model_validate(payload)


def _without_machine_specific_fields(report: RetrievalExperimentReport) -> dict[str, Any]:
    value = report.model_dump(mode="json")
    for field in ("generated_at", "dataset_path", "software_versions", "setup_latency_ms"):
        value.pop(field)
    for metric_name in ("mean_latency_ms", "p50_latency_ms", "p95_latency_ms"):
        value["metrics"].pop(metric_name)
        for slice_value in value["slices"]:
            slice_value["metrics"].pop(metric_name)
    for query in value["queries"]:
        query.pop("latency_ms")
    return value
