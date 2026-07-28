import json
import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from rag_pymc.domain import Difficulty
from rag_pymc.evaluation.dataset import load_evaluation_queries
from rag_pymc.evaluation.errors import EvaluationDatasetError
from rag_pymc.evaluation.metrics import (
    ndcg_at_k,
    percentile,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from rag_pymc.evaluation.retrieval_models import EvaluationQuery


def test_binary_retrieval_metrics_match_hand_calculation() -> None:
    retrieved = ["a", "x", "b"]
    relevant = {"a", "b"}

    assert recall_at_k(retrieved, relevant, 3) == 1.0
    assert precision_at_k(retrieved, relevant, 3) == pytest.approx(2 / 3)
    assert reciprocal_rank(retrieved, relevant, 3) == 1.0
    expected_ndcg = (1 + 1 / math.log2(4)) / (1 + 1 / math.log2(3))
    assert ndcg_at_k(retrieved, relevant, 3) == pytest.approx(expected_ndcg)


def test_metrics_handle_misses_and_interpolated_percentiles() -> None:
    assert recall_at_k(["x"], {"a"}, 1) == 0.0
    assert precision_at_k([], {"a"}, 3) == 0.0
    assert reciprocal_rank(["x"], {"a"}, 1) == 0.0
    assert ndcg_at_k([], {"a"}, 3) == 0.0
    assert percentile([1.0, 3.0], 0.5) == 2.0
    assert percentile([], 0.95) == 0.0


def test_evaluation_query_requires_qrels_only_when_answerable() -> None:
    with pytest.raises(ValidationError, match="require at least one relevant_chunk_id"):
        EvaluationQuery(
            question_id="q1",
            question="What is sampling?",
            intent="api_lookup",
            answerable=True,
            difficulty=Difficulty.BEGINNER,
        )

    with pytest.raises(ValidationError, match="cannot declare relevant"):
        EvaluationQuery(
            question_id="q2",
            question="Not in corpus?",
            intent="unanswerable",
            answerable=False,
            relevant_chunk_ids=("chunk_a",),
            difficulty=Difficulty.BEGINNER,
        )


def test_dataset_loader_rejects_duplicate_question_ids(tmp_path: Path) -> None:
    item = {
        "question_id": "q1",
        "question": "What is sampling?",
        "intent": "api_lookup",
        "answerable": True,
        "relevant_chunk_ids": ["chunk_a"],
        "difficulty": "beginner",
    }
    dataset = tmp_path / "queries.jsonl"
    dataset.write_text(f"{json.dumps(item)}\n{json.dumps(item)}\n", encoding="utf-8")

    with pytest.raises(EvaluationDatasetError, match="duplicate question_id"):
        load_evaluation_queries(dataset)
