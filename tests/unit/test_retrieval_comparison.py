from datetime import UTC, datetime
from pathlib import Path

import pytest

from rag_pymc.evaluation import (
    DenseRetrievalExperimentConfig,
    EvaluationError,
    RetrievalExperimentConfig,
    compare_retrieval_reports,
    write_comparison_report,
)
from rag_pymc.evaluation.models import (
    AggregateRetrievalMetrics,
    QueryEvaluationResult,
    RetrievalExperimentReport,
    RetrievalMetricsSlice,
)


def make_metrics(*, mrr: float) -> AggregateRetrievalMetrics:
    return AggregateRetrievalMetrics(
        query_count=1,
        answerable_query_count=1,
        unanswerable_query_count=0,
        recall_at_k=1.0,
        precision_at_k=1 / 3,
        hit_rate_at_k=1.0,
        mrr=mrr,
        ndcg_at_k=mrr,
        correct_abstention_rate=0.0,
        version_correctness=1.0,
        mean_latency_ms=1.0,
        p50_latency_ms=1.0,
        p95_latency_ms=1.0,
        mean_retrieved_tokens=10.0,
    )


def make_report(
    *,
    experiment_id: str,
    dense: bool,
    retrieved: tuple[str, ...],
    corpus_hash: str = "c" * 64,
) -> RetrievalExperimentReport:
    config: RetrievalExperimentConfig | DenseRetrievalExperimentConfig
    if dense:
        config = DenseRetrievalExperimentConfig(
            seed=1,
            top_k=3,
            retriever="dense",
            corpus_chunk_count=3,
            embedder="fake",
            model_id="fake/model",
            model_revision="a" * 40,
            dimension=2,
            normalize_embeddings=True,
            max_sequence_length=512,
            truncated_document_count=0,
            device="cpu",
            batch_size=1,
        )
    else:
        config = RetrievalExperimentConfig(
            seed=1,
            top_k=3,
            retriever="bm25",
            tokenizer="test",
            k1=1.5,
            b=0.75,
            corpus_chunk_count=3,
        )
    reciprocal_rank = 1 / (retrieved.index("relevant") + 1)
    query = QueryEvaluationResult(
        question_id="q1",
        answerable=True,
        relevant_chunk_ids=("relevant",),
        retrieved_chunk_ids=retrieved,
        scores=tuple(float(index) for index in range(len(retrieved))),
        recall_at_k=1.0,
        precision_at_k=1 / 3,
        hit_at_k=1.0,
        reciprocal_rank=reciprocal_rank,
        ndcg_at_k=reciprocal_rank,
        latency_ms=1.0,
        retrieved_tokens=10,
        version_correct=True,
        abstained=False,
        correct_abstention=None,
    )
    return RetrievalExperimentReport(
        experiment_id=experiment_id,
        generated_at=datetime(2026, 7, 19, tzinfo=UTC),
        dataset_path="dataset.jsonl",
        dataset_sha256="d" * 64,
        slices=(
            RetrievalMetricsSlice(
                dimension="intent",
                value="api_lookup",
                metrics=make_metrics(mrr=reciprocal_rank),
            ),
        ),
        corpus_sha256=corpus_hash,
        config=config,
        software_versions={"python": "test"},
        metrics=make_metrics(mrr=reciprocal_rank),
        queries=(query,),
    )


def test_comparison_reports_candidate_rank_win_and_metric_delta(tmp_path: Path) -> None:
    baseline = make_report(
        experiment_id="baseline",
        dense=False,
        retrieved=("other", "relevant", "third"),
    )
    candidate = make_report(
        experiment_id="candidate",
        dense=True,
        retrieved=("relevant", "other", "third"),
    )

    comparison = compare_retrieval_reports(baseline, candidate)
    output = tmp_path / "comparison.json"
    write_comparison_report(comparison, output)

    assert comparison.slice_comparisons[0].dimension == "intent"
    assert comparison.slice_comparisons[0].metric_deltas["mrr"] == 0.5
    assert comparison.outcome_counts == {
        "baseline_win": 0,
        "candidate_win": 1,
        "tie": 0,
    }
    assert comparison.metric_deltas["mrr"] == 0.5
    assert output.is_file()


def test_comparison_rejects_different_corpora() -> None:
    baseline = make_report(
        experiment_id="baseline",
        dense=False,
        retrieved=("relevant",),
    )
    candidate = make_report(
        experiment_id="candidate",
        dense=True,
        retrieved=("relevant",),
        corpus_hash="x" * 64,
    )

    with pytest.raises(EvaluationError, match="different corpora"):
        compare_retrieval_reports(baseline, candidate)
