import json
import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from rag_pymc.domain import Difficulty
from rag_pymc.evaluation import (
    DenseRetrievalExperimentConfig,
    EvaluationDatasetError,
    EvaluationQuery,
    HybridRetrievalExperimentConfig,
    RerankedRetrievalExperimentConfig,
    RetrievalExperimentConfig,
    load_evaluation_queries,
)
from rag_pymc.evaluation.metrics import (
    ndcg_at_k,
    percentile,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


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


def test_hybrid_config_requires_shared_cutoff_seed_and_corpus() -> None:
    sparse = RetrievalExperimentConfig(
        seed=7,
        top_k=3,
        retriever="bm25",
        tokenizer="technical",
        k1=1.5,
        b=0.75,
        corpus_chunk_count=15,
    )
    dense = DenseRetrievalExperimentConfig(
        seed=7,
        top_k=3,
        retriever="dense",
        corpus_chunk_count=15,
        embedder="fake",
        model_id="fake/model",
        model_revision="a" * 40,
        dimension=2,
        max_sequence_length=512,
        truncated_document_count=0,
        normalize_embeddings=True,
        device="cpu",
        batch_size=4,
    )
    config = HybridRetrievalExperimentConfig(
        seed=7,
        top_k=3,
        retriever="weighted-rrf-v1",
        corpus_chunk_count=15,
        candidate_k=10,
        rrf_k=60,
        sparse_weight=1.0,
        dense_weight=1.0,
        sparse=sparse,
        dense=dense,
    )

    assert config.candidate_k == 10
    invalid = config.model_dump()
    invalid["candidate_k"] = 2
    with pytest.raises(ValidationError, match="candidate_k"):
        HybridRetrievalExperimentConfig.model_validate(invalid)


def test_reranked_config_requires_shared_candidate_invariants() -> None:
    sparse = RetrievalExperimentConfig(
        seed=7,
        top_k=3,
        retriever="bm25",
        tokenizer="technical",
        k1=1.5,
        b=0.75,
        corpus_chunk_count=15,
    )
    dense = DenseRetrievalExperimentConfig(
        seed=7,
        top_k=3,
        retriever="dense",
        corpus_chunk_count=15,
        embedder="fake",
        model_id="fake/model",
        model_revision="a" * 40,
        dimension=2,
        max_sequence_length=512,
        truncated_document_count=0,
        normalize_embeddings=True,
        device="cpu",
        batch_size=4,
    )
    hybrid = HybridRetrievalExperimentConfig(
        seed=7,
        top_k=3,
        retriever="rrf",
        corpus_chunk_count=15,
        candidate_k=10,
        rrf_k=60,
        sparse_weight=1.0,
        dense_weight=1.0,
        sparse=sparse,
        dense=dense,
    )
    config = RerankedRetrievalExperimentConfig(
        seed=7,
        top_k=3,
        retriever="reranked",
        corpus_chunk_count=15,
        candidate_k=10,
        candidate=hybrid,
        reranker="fake",
        model_id="fake/reranker",
        model_revision="b" * 40,
        max_sequence_length=512,
        device="cpu",
        batch_size=4,
    )

    invalid = config.model_dump()
    invalid["candidate_k"] = 2
    with pytest.raises(ValidationError, match="candidate_k"):
        RerankedRetrievalExperimentConfig.model_validate(invalid)
