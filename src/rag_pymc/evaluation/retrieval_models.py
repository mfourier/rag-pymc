"""Contracts for deterministic retrieval datasets and experiment reports."""

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import model_validator

from rag_pymc.domain import Difficulty, SourceType
from rag_pymc.evaluation._model_base import EvaluationModel, NonEmptyString


class EvaluationQuery(EvaluationModel):
    """One manually curated retrieval question and its relevance judgments."""

    question_id: NonEmptyString
    question: NonEmptyString
    intent: NonEmptyString
    answerable: bool
    relevant_document_ids: tuple[NonEmptyString, ...] = ()
    relevant_chunk_ids: tuple[NonEmptyString, ...] = ()
    required_api_symbols: tuple[NonEmptyString, ...] = ()
    reference_answer: NonEmptyString | None = None
    expected_citations: tuple[NonEmptyString, ...] = ()
    difficulty: Difficulty
    library: NonEmptyString | None = None
    library_version: NonEmptyString | None = None
    source_types: tuple[SourceType, ...] = ()

    @model_validator(mode="after")
    def relevance_matches_answerability(self) -> Self:
        """Require qrels exactly for answerable questions."""
        if self.answerable and not self.relevant_chunk_ids:
            msg = "answerable queries require at least one relevant_chunk_id"
            raise ValueError(msg)
        if not self.answerable and (self.relevant_chunk_ids or self.relevant_document_ids):
            msg = "unanswerable queries cannot declare relevant documents or chunks"
            raise ValueError(msg)
        return self


class QueryEvaluationResult(EvaluationModel):
    """Metrics and ranking output for one evaluated query."""

    question_id: NonEmptyString
    answerable: bool
    relevant_chunk_ids: tuple[NonEmptyString, ...]
    retrieved_chunk_ids: tuple[NonEmptyString, ...]
    scores: tuple[float, ...]
    recall_at_k: float | None
    precision_at_k: float | None
    hit_at_k: float | None
    reciprocal_rank: float | None
    ndcg_at_k: float | None
    latency_ms: float
    retrieved_tokens: int
    version_correct: bool
    abstained: bool
    correct_abstention: bool | None


class AggregateRetrievalMetrics(EvaluationModel):
    """Aggregate retrieval and abstention metrics."""

    query_count: int
    answerable_query_count: int
    unanswerable_query_count: int
    recall_at_k: float
    precision_at_k: float
    hit_rate_at_k: float
    mrr: float
    ndcg_at_k: float
    correct_abstention_rate: float
    version_correctness: float
    mean_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    mean_retrieved_tokens: float


class RetrievalMetricsSlice(EvaluationModel):
    """Aggregate metrics for one intent or difficulty subset."""

    dimension: Literal["intent", "difficulty"]
    value: NonEmptyString
    metrics: AggregateRetrievalMetrics


class RetrievalExperimentConfig(EvaluationModel):
    """Parameters needed to reproduce one BM25 evaluation."""

    seed: int
    top_k: int
    retriever: NonEmptyString
    tokenizer: NonEmptyString
    k1: float
    b: float
    corpus_chunk_count: int


class RetrievalExperimentReport(EvaluationModel):
    """Complete machine-readable result of one retrieval experiment."""

    schema_version: NonEmptyString = "1"
    experiment_id: NonEmptyString
    generated_at: datetime
    dataset_path: NonEmptyString
    dataset_sha256: NonEmptyString
    corpus_sha256: NonEmptyString
    config: RetrievalExperimentConfig
    software_versions: dict[str, str]
    setup_latency_ms: float | None = None
    metrics: AggregateRetrievalMetrics
    queries: tuple[QueryEvaluationResult, ...]
    slices: tuple[RetrievalMetricsSlice, ...] = ()
    errors: tuple[str, ...] = ()
    limitations: tuple[NonEmptyString, ...] = ()

    def as_json_value(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return self.model_dump(mode="json")
