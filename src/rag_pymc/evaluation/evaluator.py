"""Execution and reporting for retrieval experiments."""

import json
import platform
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from statistics import fmean
from time import perf_counter_ns
from typing import Literal

from rag_pymc import __version__
from rag_pymc.domain import Chunk, SearchQuery
from rag_pymc.evaluation.metrics import (
    ndcg_at_k,
    percentile,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from rag_pymc.evaluation.models import (
    AggregateRetrievalMetrics,
    EvaluationQuery,
    ExperimentConfig,
    QueryEvaluationResult,
    RetrievalExperimentReport,
    RetrievalMetricsSlice,
)
from rag_pymc.retrieval import Retriever, TechnicalTokenizer


class RetrievalEvaluator:
    """Evaluate a retriever against explicit binary relevance judgments."""

    def __init__(
        self,
        *,
        retriever: Retriever,
        chunks: Sequence[Chunk],
        tokenizer: TechnicalTokenizer,
        config: ExperimentConfig,
        experiment_id: str = "phase2-bm25-baseline",
        limitations: Sequence[str] | None = None,
        setup_latency_ms: float | None = None,
    ) -> None:
        """Configure evaluation dependencies and immutable experiment settings."""
        self._retriever = retriever
        self._chunks = tuple(chunks)
        self._tokenizer = tokenizer
        self._config = config
        self._experiment_id = experiment_id
        self._limitations = (
            tuple(limitations)
            if limitations is not None
            else (
                "The corpus contains one PyMC API page and five semantic chunks.",
                "Binary qrels were curated for pipeline validation, not broad retrieval claims.",
                "No score threshold or learned abstention policy is applied.",
                "Latency measures an in-process index over a five-chunk corpus.",
            )
        )
        self._setup_latency_ms = setup_latency_ms

    def evaluate(
        self,
        queries: Sequence[EvaluationQuery],
        *,
        dataset_path: Path,
        generated_at: datetime | None = None,
    ) -> RetrievalExperimentReport:
        """Run every query and return aggregate and per-query measurements."""
        results = tuple(self._evaluate_query(query) for query in queries)
        metrics = self._aggregate(results)
        slices = self._slice_metrics(queries, results)
        return RetrievalExperimentReport(
            experiment_id=self._experiment_id,
            generated_at=generated_at or datetime.now(UTC),
            dataset_path=dataset_path.as_posix(),
            dataset_sha256=sha256(dataset_path.read_bytes()).hexdigest(),
            corpus_sha256=self._corpus_hash(),
            config=self._config,
            software_versions=self._software_versions(),
            setup_latency_ms=self._setup_latency_ms,
            slices=slices,
            metrics=metrics,
            queries=results,
            limitations=self._limitations,
        )

    def _evaluate_query(self, item: EvaluationQuery) -> QueryEvaluationResult:
        query = SearchQuery(
            text=item.question,
            top_k=self._config.top_k,
            library=item.library,
            library_version=item.library_version,
            source_types=item.source_types,
        )
        started_at = perf_counter_ns()
        retrieved = self._retriever.retrieve(query)
        latency_ms = (perf_counter_ns() - started_at) / 1_000_000
        retrieved_ids = tuple(result.chunk.chunk_id for result in retrieved)
        relevant = set(item.relevant_chunk_ids)
        abstained = not retrieved
        version_correct = all(
            (item.library is None or result.chunk.library.casefold() == item.library.casefold())
            and (
                item.library_version is None or result.chunk.library_version == item.library_version
            )
            for result in retrieved
        )
        return QueryEvaluationResult(
            question_id=item.question_id,
            answerable=item.answerable,
            relevant_chunk_ids=item.relevant_chunk_ids,
            retrieved_chunk_ids=retrieved_ids,
            scores=tuple(result.score for result in retrieved),
            recall_at_k=recall_at_k(retrieved_ids, relevant, self._config.top_k)
            if item.answerable
            else None,
            precision_at_k=precision_at_k(retrieved_ids, relevant, self._config.top_k)
            if item.answerable
            else None,
            hit_at_k=float(bool(set(retrieved_ids) & relevant)) if item.answerable else None,
            reciprocal_rank=reciprocal_rank(retrieved_ids, relevant, self._config.top_k)
            if item.answerable
            else None,
            ndcg_at_k=ndcg_at_k(retrieved_ids, relevant, self._config.top_k)
            if item.answerable
            else None,
            latency_ms=latency_ms,
            retrieved_tokens=sum(
                len(self._tokenizer.tokenize(result.chunk.content)) for result in retrieved
            ),
            version_correct=version_correct,
            abstained=abstained,
            correct_abstention=abstained if not item.answerable else None,
        )

    def _aggregate(
        self,
        results: Sequence[QueryEvaluationResult],
    ) -> AggregateRetrievalMetrics:
        answerable = tuple(result for result in results if result.answerable)
        unanswerable = tuple(result for result in results if not result.answerable)
        all_retrieved = sum(len(result.retrieved_chunk_ids) for result in results)
        version_correct_retrieved = sum(
            len(result.retrieved_chunk_ids) if result.version_correct else 0 for result in results
        )
        latencies = [result.latency_ms for result in results]
        return AggregateRetrievalMetrics(
            query_count=len(results),
            answerable_query_count=len(answerable),
            unanswerable_query_count=len(unanswerable),
            recall_at_k=self._mean_optional(answerable, "recall_at_k"),
            precision_at_k=self._mean_optional(answerable, "precision_at_k"),
            hit_rate_at_k=self._mean_optional(answerable, "hit_at_k"),
            mrr=self._mean_optional(answerable, "reciprocal_rank"),
            ndcg_at_k=self._mean_optional(answerable, "ndcg_at_k"),
            correct_abstention_rate=(
                fmean(float(result.correct_abstention is True) for result in unanswerable)
                if unanswerable
                else 0.0
            ),
            version_correctness=(
                version_correct_retrieved / all_retrieved if all_retrieved else 1.0
            ),
            mean_latency_ms=fmean(latencies) if latencies else 0.0,
            p50_latency_ms=percentile(latencies, 0.50),
            p95_latency_ms=percentile(latencies, 0.95),
            mean_retrieved_tokens=(
                fmean(result.retrieved_tokens for result in results) if results else 0.0
            ),
        )

    def _slice_metrics(
        self,
        queries: Sequence[EvaluationQuery],
        results: Sequence[QueryEvaluationResult],
    ) -> tuple[RetrievalMetricsSlice, ...]:
        grouped: defaultdict[
            tuple[Literal["intent", "difficulty"], str], list[QueryEvaluationResult]
        ] = defaultdict(list)
        for query, result in zip(queries, results, strict=True):
            grouped[("intent", query.intent)].append(result)
            grouped[("difficulty", query.difficulty.value)].append(result)
        return tuple(
            RetrievalMetricsSlice(
                dimension=dimension,
                value=value,
                metrics=self._aggregate(grouped[(dimension, value)]),
            )
            for dimension, value in sorted(grouped)
        )

    def _corpus_hash(self) -> str:
        identity = "\n".join(
            f"{chunk.chunk_id}:{chunk.content_hash}"
            for chunk in sorted(self._chunks, key=lambda c: c.chunk_id)
        )
        return sha256(identity.encode("utf-8")).hexdigest()

    @staticmethod
    def _mean_optional(results: Sequence[QueryEvaluationResult], field: str) -> float:
        values = [getattr(result, field) for result in results]
        numeric = [float(value) for value in values if value is not None]
        return fmean(numeric) if numeric else 0.0

    @staticmethod
    def _software_versions() -> dict[str, str]:
        distributions = (
            "rag-pymc",
            "pymc",
            "arviz",
            "pytensor",
            "pydantic",
            "sentence-transformers",
            "torch",
            "transformers",
        )
        versions: dict[str, str] = {"python": platform.python_version(), "rag-pymc": __version__}
        for distribution in distributions[1:]:
            try:
                versions[distribution] = version(distribution)
            except PackageNotFoundError:
                versions[distribution] = "not-installed"
        return versions


def write_experiment_report(report: RetrievalExperimentReport, path: Path) -> None:
    """Write a readable machine-validated experiment artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report.as_json_value(), indent=2, sort_keys=True)
    path.write_text(f"{serialized}\n", encoding="utf-8")
