"""Lock the selected BM25 baseline to its frozen corpus and judgments."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "datasets/evaluation/phase4/pymc_core_queries.jsonl"
BASELINE_PATH = PROJECT_ROOT / "reports/evaluation/phase4-bm25-expanded.json"
SOURCE_NAMES = (
    "pymc.sample",
    "pymc.Data",
    "pymc.model.core.set_data",
    "pymc.sample_posterior_predictive",
)


def test_selected_bm25_baseline_reproduces_exact_non_latency_results(tmp_path: Path) -> None:
    repository = JsonDocumentRepository(tmp_path / "corpus")
    for source_name in SOURCE_NAMES:
        manifest_path = PROJECT_ROOT / f"datasets/raw/manifests/pymc/6.1.0/{source_name}.json"
        source_path = PROJECT_ROOT / f"datasets/fixtures/pymc/6.1.0/{source_name}.html"
        manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        IngestionService(
            fetcher=LocalFileSourceFetcher(source_path),
            parser=SphinxApiParser(),
            chunker=ApiReferenceChunker(),
            repository=repository,
        ).run(manifest)

    recorded = RetrievalExperimentReport.model_validate_json(
        BASELINE_PATH.read_text(encoding="utf-8")
    )
    chunks = repository.load_chunks()
    runtime = build_sparse_runtime(chunks, k1=recorded.config.k1, b=recorded.config.b)
    config = build_sparse_experiment_config(
        chunks,
        index=runtime.index,
        tokenizer=runtime.tokenizer,
        seed=recorded.config.seed,
        top_k=recorded.config.top_k,
    )
    rebuilt = RetrievalEvaluator(
        retriever=runtime.retriever,
        chunks=chunks,
        tokenizer=runtime.tokenizer,
        config=config,
        experiment_id=recorded.experiment_id,
        limitations=recorded.limitations,
    ).evaluate(
        load_evaluation_queries(DATASET_PATH),
        dataset_path=DATASET_PATH,
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )

    assert _without_machine_specific_fields(rebuilt) == _without_machine_specific_fields(recorded)


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
