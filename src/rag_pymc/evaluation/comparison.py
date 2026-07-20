"""Pairwise retrieval comparison artifacts."""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rag_pymc.evaluation.errors import EvaluationError
from rag_pymc.evaluation.models import (
    AggregateRetrievalMetrics,
    EvaluationModel,
    ExperimentConfig,
    NonEmptyString,
    QueryEvaluationResult,
    RetrievalExperimentReport,
    RetrievalMetricsSlice,
)


class QueryRankComparison(EvaluationModel):
    """First-relevant-rank outcome for one shared evaluation query."""

    question_id: NonEmptyString
    answerable: bool
    baseline_first_relevant_rank: int | None
    candidate_first_relevant_rank: int | None
    outcome: NonEmptyString


class RetrievalSliceComparison(EvaluationModel):
    """Metric deltas for one shared intent or difficulty slice."""

    dimension: NonEmptyString
    value: NonEmptyString
    query_count: int
    metric_deltas: dict[str, float]


class RetrievalComparisonReport(EvaluationModel):
    """Machine-readable comparison of two compatible retrieval reports."""

    schema_version: NonEmptyString = "1"
    experiment_id: NonEmptyString
    generated_at: datetime
    dataset_sha256: NonEmptyString
    corpus_sha256: NonEmptyString
    baseline_experiment_id: NonEmptyString
    candidate_experiment_id: NonEmptyString
    baseline_config: ExperimentConfig
    candidate_config: ExperimentConfig
    baseline_software_versions: dict[str, str]
    candidate_software_versions: dict[str, str]
    baseline_metrics: AggregateRetrievalMetrics
    candidate_metrics: AggregateRetrievalMetrics
    metric_deltas: dict[str, float]
    query_outcomes: tuple[QueryRankComparison, ...]
    slice_comparisons: tuple[RetrievalSliceComparison, ...]
    outcome_counts: dict[str, int]
    observations: tuple[NonEmptyString, ...]
    errors: tuple[str, ...] = ()
    limitations: tuple[NonEmptyString, ...] = ()

    def as_json_value(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return self.model_dump(mode="json")


def compare_retrieval_reports(
    baseline: RetrievalExperimentReport,
    candidate: RetrievalExperimentReport,
    *,
    generated_at: datetime | None = None,
    experiment_id: str = "phase3-sparse-vs-dense",
    limitations: Sequence[str] | None = None,
) -> RetrievalComparisonReport:
    """Compare reports that use the same dataset, corpus, cutoff, and query IDs."""
    _validate_compatibility(baseline, candidate)
    baseline_queries = {item.question_id: item for item in baseline.queries}
    candidate_queries = {item.question_id: item for item in candidate.queries}
    outcomes = tuple(
        _compare_query(baseline_queries[question_id], candidate_queries[question_id])
        for question_id in sorted(baseline_queries)
    )
    outcome_counts = {
        outcome: sum(item.outcome == outcome for item in outcomes)
        for outcome in ("baseline_win", "candidate_win", "tie")
    }
    deltas = _metric_deltas(baseline.metrics, candidate.metrics)
    slice_comparisons = _compare_slices(baseline.slices, candidate.slices)
    return RetrievalComparisonReport(
        experiment_id=experiment_id,
        generated_at=generated_at or datetime.now(UTC),
        dataset_sha256=baseline.dataset_sha256,
        corpus_sha256=baseline.corpus_sha256,
        baseline_experiment_id=baseline.experiment_id,
        candidate_experiment_id=candidate.experiment_id,
        baseline_config=baseline.config,
        candidate_config=candidate.config,
        baseline_software_versions=baseline.software_versions,
        candidate_software_versions=candidate.software_versions,
        baseline_metrics=baseline.metrics,
        candidate_metrics=candidate.metrics,
        metric_deltas=deltas,
        query_outcomes=outcomes,
        outcome_counts=outcome_counts,
        slice_comparisons=slice_comparisons,
        observations=(
            (
                f"Candidate wins {outcome_counts['candidate_win']} queries, baseline wins "
                f"{outcome_counts['baseline_win']}, and {outcome_counts['tie']} are tied."
            ),
            f"Candidate MRR delta is {deltas['mrr']:.6f}.",
            (f"Candidate correct-abstention delta is {deltas['correct_abstention_rate']:.6f}."),
        ),
        limitations=(
            tuple(limitations)
            if limitations is not None
            else (
                "Both retrievers are evaluated on one API page and five chunks.",
                "The dataset was designed around this corpus and is not an external benchmark.",
                "Latency compares different algorithms but excludes one-time model download.",
            )
        ),
    )


def write_comparison_report(report: RetrievalComparisonReport, path: Path) -> None:
    """Write a validated pairwise retrieval comparison report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report.as_json_value(), indent=2, sort_keys=True)
    path.write_text(f"{serialized}\n", encoding="utf-8")


def _validate_compatibility(
    baseline: RetrievalExperimentReport,
    candidate: RetrievalExperimentReport,
) -> None:
    if baseline.dataset_sha256 != candidate.dataset_sha256:
        msg = "cannot compare reports from different evaluation datasets"
        raise EvaluationError(msg)
    if baseline.corpus_sha256 != candidate.corpus_sha256:
        msg = "cannot compare reports from different corpora"
        raise EvaluationError(msg)
    if baseline.config.top_k != candidate.config.top_k:
        msg = "cannot compare reports with different top_k values"
        raise EvaluationError(msg)
    baseline_ids = {item.question_id for item in baseline.queries}
    candidate_ids = {item.question_id for item in candidate.queries}
    if baseline_ids != candidate_ids:
        msg = "cannot compare reports with different query IDs"
        raise EvaluationError(msg)


def _compare_slices(
    baseline: Sequence[RetrievalMetricsSlice],
    candidate: Sequence[RetrievalMetricsSlice],
) -> tuple[RetrievalSliceComparison, ...]:
    baseline_by_key = {(item.dimension, item.value): item for item in baseline}
    candidate_by_key = {(item.dimension, item.value): item for item in candidate}
    if baseline_by_key.keys() != candidate_by_key.keys():
        msg = "cannot compare reports with different metric slices"
        raise EvaluationError(msg)
    comparisons: list[RetrievalSliceComparison] = []
    for dimension, value in sorted(baseline_by_key):
        baseline_slice = baseline_by_key[(dimension, value)]
        candidate_slice = candidate_by_key[(dimension, value)]
        if baseline_slice.metrics.query_count != candidate_slice.metrics.query_count:
            msg = f"query count mismatch for {dimension}={value}"
            raise EvaluationError(msg)
        comparisons.append(
            RetrievalSliceComparison(
                dimension=dimension,
                value=value,
                query_count=baseline_slice.metrics.query_count,
                metric_deltas=_metric_deltas(
                    baseline_slice.metrics,
                    candidate_slice.metrics,
                ),
            )
        )
    return tuple(comparisons)


def _metric_deltas(
    baseline: AggregateRetrievalMetrics,
    candidate: AggregateRetrievalMetrics,
) -> dict[str, float]:
    return {
        field: getattr(candidate, field) - getattr(baseline, field)
        for field in (
            "recall_at_k",
            "precision_at_k",
            "hit_rate_at_k",
            "mrr",
            "ndcg_at_k",
            "correct_abstention_rate",
            "version_correctness",
            "mean_latency_ms",
            "mean_retrieved_tokens",
        )
    }


def _compare_query(
    baseline: QueryEvaluationResult,
    candidate: QueryEvaluationResult,
) -> QueryRankComparison:
    if baseline.answerable != candidate.answerable:
        msg = f"answerability mismatch for {baseline.question_id}"
        raise EvaluationError(msg)

    if baseline.answerable:
        baseline_rank = _first_relevant_rank(baseline)
        candidate_rank = _first_relevant_rank(candidate)
        outcome = _rank_outcome(baseline_rank, candidate_rank)
    else:
        baseline_rank = None
        candidate_rank = None
        outcome = _abstention_outcome(baseline.correct_abstention, candidate.correct_abstention)

    return QueryRankComparison(
        question_id=baseline.question_id,
        answerable=baseline.answerable,
        baseline_first_relevant_rank=baseline_rank,
        candidate_first_relevant_rank=candidate_rank,
        outcome=outcome,
    )


def _first_relevant_rank(result: QueryEvaluationResult) -> int | None:
    relevant = set(result.relevant_chunk_ids)
    return next(
        (
            rank
            for rank, chunk_id in enumerate(result.retrieved_chunk_ids, start=1)
            if chunk_id in relevant
        ),
        None,
    )


def _rank_outcome(baseline_rank: int | None, candidate_rank: int | None) -> str:
    if baseline_rank == candidate_rank:
        return "tie"
    if baseline_rank is None:
        return "candidate_win"
    if candidate_rank is None:
        return "baseline_win"
    return "candidate_win" if candidate_rank < baseline_rank else "baseline_win"


def _abstention_outcome(baseline: bool | None, candidate: bool | None) -> str:
    if baseline == candidate:
        return "tie"
    return "candidate_win" if candidate is True else "baseline_win"
