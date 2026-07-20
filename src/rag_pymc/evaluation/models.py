"""Validated contracts for retrieval datasets and experiment reports."""

from datetime import datetime
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from rag_pymc.domain import Difficulty, SourceType

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


class EvaluationModel(BaseModel):
    """Strict immutable base for evaluation artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


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


class DenseRetrievalExperimentConfig(EvaluationModel):
    """Parameters needed to reproduce one dense retrieval evaluation."""

    seed: int
    top_k: int
    retriever: NonEmptyString
    corpus_chunk_count: int
    embedder: NonEmptyString
    model_id: NonEmptyString
    model_revision: NonEmptyString
    dimension: int = Field(gt=0)
    max_sequence_length: int = Field(gt=0)
    truncated_document_count: int = Field(ge=0)
    normalize_embeddings: bool
    query_prefix: NonEmptyString | None = None
    device: NonEmptyString
    batch_size: int = Field(gt=0)


class HybridRetrievalExperimentConfig(EvaluationModel):
    """Parameters needed to reproduce weighted Reciprocal Rank Fusion."""

    seed: int
    top_k: int = Field(gt=0)
    retriever: NonEmptyString
    corpus_chunk_count: int = Field(gt=0)
    candidate_k: int = Field(gt=0)
    rrf_k: int = Field(gt=0)
    sparse_weight: float = Field(gt=0)
    dense_weight: float = Field(gt=0)
    sparse: RetrievalExperimentConfig
    dense: DenseRetrievalExperimentConfig

    @model_validator(mode="after")
    def validate_component_configuration(self) -> Self:
        """Require one shared cutoff, seed, and corpus across all experiment arms."""
        if self.candidate_k < self.top_k:
            msg = "candidate_k must be greater than or equal to top_k"
            raise ValueError(msg)
        for name, component in (("sparse", self.sparse), ("dense", self.dense)):
            if component.seed != self.seed:
                msg = f"{name} seed does not match hybrid seed"
                raise ValueError(msg)
            if component.top_k != self.top_k:
                msg = f"{name} top_k does not match hybrid top_k"
                raise ValueError(msg)
            if component.corpus_chunk_count != self.corpus_chunk_count:
                msg = f"{name} corpus size does not match hybrid corpus size"
                raise ValueError(msg)
        return self


class RerankedRetrievalExperimentConfig(EvaluationModel):
    """Parameters needed to reproduce cross-encoder reranking."""

    seed: int
    top_k: int = Field(gt=0)
    retriever: NonEmptyString
    corpus_chunk_count: int = Field(gt=0)
    candidate_k: int = Field(gt=0)
    candidate: HybridRetrievalExperimentConfig
    reranker: NonEmptyString
    model_id: NonEmptyString
    model_revision: NonEmptyString
    max_sequence_length: int = Field(gt=0)
    device: NonEmptyString
    batch_size: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_candidate_configuration(self) -> Self:
        """Require the reranked and candidate arms to share experiment invariants."""
        if self.candidate_k < self.top_k:
            msg = "candidate_k must be greater than or equal to top_k"
            raise ValueError(msg)
        if self.candidate.seed != self.seed:
            msg = "candidate seed does not match reranking seed"
            raise ValueError(msg)
        if self.candidate.top_k != self.top_k:
            msg = "candidate top_k does not match reranking top_k"
            raise ValueError(msg)
        if self.candidate.corpus_chunk_count != self.corpus_chunk_count:
            msg = "candidate corpus size does not match reranking corpus size"
            raise ValueError(msg)
        return self


type ExperimentConfig = (
    RetrievalExperimentConfig
    | DenseRetrievalExperimentConfig
    | HybridRetrievalExperimentConfig
    | RerankedRetrievalExperimentConfig
)


class RetrievalExperimentReport(EvaluationModel):
    """Complete machine-readable result of one retrieval experiment."""

    schema_version: NonEmptyString = "1"
    experiment_id: NonEmptyString
    generated_at: datetime
    dataset_path: NonEmptyString
    dataset_sha256: NonEmptyString
    corpus_sha256: NonEmptyString
    config: ExperimentConfig
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
