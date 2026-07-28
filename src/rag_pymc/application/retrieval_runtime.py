"""Runtime composition for the selected local BM25 retrieval policy."""

from collections.abc import Sequence
from dataclasses import dataclass

from rag_pymc.domain import Chunk
from rag_pymc.evaluation.retrieval_models import RetrievalExperimentConfig
from rag_pymc.indexing import BM25Index
from rag_pymc.retrieval import SparseRetriever, TechnicalTokenizer


@dataclass(frozen=True, slots=True)
class SparseRuntime:
    """Fully configured deterministic BM25 retrieval stack."""

    tokenizer: TechnicalTokenizer
    index: BM25Index
    retriever: SparseRetriever


def build_sparse_experiment_config(
    chunks: Sequence[Chunk],
    *,
    index: BM25Index,
    tokenizer: TechnicalTokenizer,
    seed: int,
    top_k: int,
) -> RetrievalExperimentConfig:
    """Describe the exact sparse runtime used by an evaluation."""
    return RetrievalExperimentConfig(
        seed=seed,
        top_k=top_k,
        retriever=index.name,
        tokenizer=tokenizer.name,
        k1=index.k1,
        b=index.b,
        corpus_chunk_count=len(chunks),
    )


def build_sparse_runtime(
    chunks: Sequence[Chunk],
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> SparseRuntime:
    """Build the selected deterministic BM25 retrieval stack."""
    tokenizer = TechnicalTokenizer()
    index = BM25Index(chunks, tokenizer=tokenizer, k1=k1, b=b)
    return SparseRuntime(
        tokenizer=tokenizer,
        index=index,
        retriever=SparseRetriever(index),
    )
