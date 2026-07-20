"""Retrieval evaluation datasets, metrics, and experiment runner."""

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
    DenseRetrievalExperimentConfig,
    EvaluationQuery,
    ExperimentConfig,
    HybridRetrievalExperimentConfig,
    QueryEvaluationResult,
    RerankedRetrievalExperimentConfig,
    RetrievalExperimentConfig,
    RetrievalExperimentReport,
    RetrievalMetricsSlice,
)

__all__ = [
    "AggregateRetrievalMetrics",
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
    "compare_retrieval_reports",
    "load_evaluation_queries",
    "write_comparison_report",
    "write_experiment_report",
]
