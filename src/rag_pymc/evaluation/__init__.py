"""Versioned retrieval and structural response evaluation contracts."""

from rag_pymc.evaluation.comparison import (
    QueryRankComparison,
    RetrievalComparisonReport,
    RetrievalSliceComparison,
    compare_retrieval_reports,
    write_comparison_report,
)
from rag_pymc.evaluation.dataset import load_evaluation_queries
from rag_pymc.evaluation.errors import EvaluationDatasetError, EvaluationError
from rag_pymc.evaluation.evaluator import RetrievalEvaluator, write_experiment_report
from rag_pymc.evaluation.models import (
    AggregateRetrievalMetrics,
    AggregateStructuralResponseMetrics,
    CitationTraceabilityReason,
    CitationTraceabilityResult,
    DenseRetrievalExperimentConfig,
    EvaluationQuery,
    ExperimentConfig,
    HybridRetrievalExperimentConfig,
    QueryEvaluationResult,
    RerankedRetrievalExperimentConfig,
    RetrievalExperimentConfig,
    RetrievalExperimentReport,
    RetrievalMetricsSlice,
    StructuralFailureReason,
    StructuralResponseAggregateReport,
    StructuralResponseEvaluation,
    StructuralValidationFailure,
    StructuralValidationStage,
)
from rag_pymc.evaluation.structural_response import (
    aggregate_structural_responses,
    evaluate_structural_response,
)

__all__ = [
    "AggregateRetrievalMetrics",
    "AggregateStructuralResponseMetrics",
    "CitationTraceabilityReason",
    "CitationTraceabilityResult",
    "DenseRetrievalExperimentConfig",
    "EvaluationDatasetError",
    "EvaluationError",
    "EvaluationQuery",
    "ExperimentConfig",
    "HybridRetrievalExperimentConfig",
    "QueryEvaluationResult",
    "QueryRankComparison",
    "RerankedRetrievalExperimentConfig",
    "RetrievalComparisonReport",
    "RetrievalEvaluator",
    "RetrievalExperimentConfig",
    "RetrievalExperimentReport",
    "RetrievalMetricsSlice",
    "RetrievalSliceComparison",
    "StructuralFailureReason",
    "StructuralResponseAggregateReport",
    "StructuralResponseEvaluation",
    "StructuralValidationFailure",
    "StructuralValidationStage",
    "aggregate_structural_responses",
    "compare_retrieval_reports",
    "evaluate_structural_response",
    "load_evaluation_queries",
    "write_comparison_report",
    "write_experiment_report",
]
