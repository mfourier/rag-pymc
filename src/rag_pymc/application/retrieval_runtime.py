"""Runtime composition for local retrieval and evaluation workflows."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns

from rag_pymc.domain import Chunk
from rag_pymc.embeddings import EmbeddingModelSpec, load_embedding_model_spec
from rag_pymc.evaluation import (
    DenseRetrievalExperimentConfig,
    HybridRetrievalExperimentConfig,
    RerankedRetrievalExperimentConfig,
    RetrievalExperimentConfig,
)
from rag_pymc.indexing import BM25Index, ExactCosineIndex
from rag_pymc.reranking import (
    RerankedRetriever,
    RerankingModelSpec,
    load_reranking_model_spec,
)
from rag_pymc.retrieval import (
    DenseRetriever,
    ReciprocalRankFusionRetriever,
    Retriever,
    SparseRetriever,
    TechnicalTokenizer,
    WeightedRetriever,
)


@dataclass(frozen=True, slots=True)
class HybridRuntime:
    """Fully configured weighted-RRF retrieval stack."""

    embedding_spec: EmbeddingModelSpec
    tokenizer: TechnicalTokenizer
    retriever: Retriever
    setup_latency_ms: float


@dataclass(frozen=True, slots=True)
class RerankingRuntime:
    """Fully configured candidate and reranked retrieval stack."""

    embedding_spec: EmbeddingModelSpec
    reranking_spec: RerankingModelSpec
    tokenizer: TechnicalTokenizer
    candidate_retriever: Retriever
    reranked_retriever: Retriever
    candidate_config: HybridRetrievalExperimentConfig
    reranked_config: RerankedRetrievalExperimentConfig
    candidate_setup_latency_ms: float
    setup_latency_ms: float
    truncated_document_count: int


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


def build_dense_experiment_config(
    chunks: Sequence[Chunk],
    *,
    index: ExactCosineIndex,
    spec: EmbeddingModelSpec,
    truncated_document_count: int,
    seed: int,
    top_k: int,
    device: str,
    batch_size: int,
) -> DenseRetrievalExperimentConfig:
    """Describe the exact dense runtime used by an evaluation."""
    return DenseRetrievalExperimentConfig(
        seed=seed,
        top_k=top_k,
        retriever=index.name,
        corpus_chunk_count=len(chunks),
        embedder=index.embedder.name,
        model_id=spec.model_id,
        model_revision=spec.revision,
        dimension=spec.dimension,
        max_sequence_length=spec.max_sequence_length,
        truncated_document_count=truncated_document_count,
        normalize_embeddings=spec.normalize_embeddings,
        query_prefix=spec.query_prefix,
        device=device,
        batch_size=batch_size,
    )


def build_hybrid_experiment_config(
    chunks: Sequence[Chunk],
    *,
    retriever_name: str,
    sparse: RetrievalExperimentConfig,
    dense: DenseRetrievalExperimentConfig,
    candidate_k: int,
    rrf_k: int,
    sparse_weight: float,
    dense_weight: float,
    seed: int,
    top_k: int,
) -> HybridRetrievalExperimentConfig:
    """Describe the exact weighted-RRF runtime used by an evaluation."""
    return HybridRetrievalExperimentConfig(
        seed=seed,
        top_k=top_k,
        retriever=retriever_name,
        corpus_chunk_count=len(chunks),
        candidate_k=candidate_k,
        rrf_k=rrf_k,
        sparse_weight=sparse_weight,
        dense_weight=dense_weight,
        sparse=sparse,
        dense=dense,
    )


def build_hybrid_runtime(
    chunks: Sequence[Chunk],
    *,
    embedding_manifest: Path,
    candidate_k: int,
    rrf_k: int,
    sparse_weight: float,
    dense_weight: float,
    seed: int,
    device: str,
    batch_size: int,
    local_files_only: bool,
) -> HybridRuntime:
    """Build the selected weighted-RRF retrieval stack."""
    from rag_pymc.embeddings.sentence_transformer import SentenceTransformerEmbedder

    embedding_spec = load_embedding_model_spec(embedding_manifest)
    setup_started_at = perf_counter_ns()
    tokenizer = TechnicalTokenizer()
    sparse_index = BM25Index(chunks, tokenizer=tokenizer, k1=1.5, b=0.75)
    embedder = SentenceTransformerEmbedder(
        embedding_spec,
        device=device,
        batch_size=batch_size,
        seed=seed,
        local_files_only=local_files_only,
    )
    dense_index = ExactCosineIndex(chunks, embedder=embedder)
    retriever = ReciprocalRankFusionRetriever(
        (
            WeightedRetriever("sparse", SparseRetriever(sparse_index), sparse_weight),
            WeightedRetriever("dense", DenseRetriever(dense_index), dense_weight),
        ),
        rrf_k=rrf_k,
        candidate_k=candidate_k,
    )
    setup_latency_ms = (perf_counter_ns() - setup_started_at) / 1_000_000
    return HybridRuntime(
        embedding_spec=embedding_spec,
        tokenizer=tokenizer,
        retriever=retriever,
        setup_latency_ms=setup_latency_ms,
    )


def build_reranking_runtime(
    chunks: Sequence[Chunk],
    *,
    embedding_manifest: Path,
    reranking_manifest: Path,
    top_k: int,
    fusion_candidate_k: int,
    rerank_candidate_k: int,
    rrf_k: int,
    sparse_weight: float,
    dense_weight: float,
    seed: int,
    device: str,
    embedding_batch_size: int,
    reranking_batch_size: int,
    local_files_only: bool,
) -> RerankingRuntime:
    """Build the fixed candidate generator and cross-encoder stage."""
    from rag_pymc.embeddings.sentence_transformer import SentenceTransformerEmbedder
    from rag_pymc.reranking.sentence_transformer import (
        SentenceTransformerCrossEncoderReranker,
    )

    embedding_spec = load_embedding_model_spec(embedding_manifest)
    reranking_spec = load_reranking_model_spec(reranking_manifest)
    tokenizer = TechnicalTokenizer()
    setup_started_at = perf_counter_ns()

    sparse_index = BM25Index(chunks, tokenizer=tokenizer, k1=1.5, b=0.75)
    embedder = SentenceTransformerEmbedder(
        embedding_spec,
        device=device,
        batch_size=embedding_batch_size,
        seed=seed,
        local_files_only=local_files_only,
    )
    dense_index = ExactCosineIndex(chunks, embedder=embedder)
    candidate_retriever = ReciprocalRankFusionRetriever(
        (
            WeightedRetriever("sparse", SparseRetriever(sparse_index), sparse_weight),
            WeightedRetriever("dense", DenseRetriever(dense_index), dense_weight),
        ),
        rrf_k=rrf_k,
        candidate_k=fusion_candidate_k,
    )
    candidate_setup_latency_ms = (perf_counter_ns() - setup_started_at) / 1_000_000

    reranker = SentenceTransformerCrossEncoderReranker(
        reranking_spec,
        device=device,
        batch_size=reranking_batch_size,
        seed=seed,
        local_files_only=local_files_only,
    )
    reranked_retriever = RerankedRetriever(
        candidate_retriever,
        reranker,
        candidate_k=rerank_candidate_k,
    )
    setup_latency_ms = (perf_counter_ns() - setup_started_at) / 1_000_000
    truncated_document_count = sum(
        embedder.token_count(chunk.content) > embedding_spec.max_sequence_length for chunk in chunks
    )

    sparse_config = build_sparse_experiment_config(
        chunks,
        index=sparse_index,
        tokenizer=tokenizer,
        seed=seed,
        top_k=top_k,
    )
    dense_config = build_dense_experiment_config(
        chunks,
        index=dense_index,
        spec=embedding_spec,
        truncated_document_count=truncated_document_count,
        seed=seed,
        top_k=top_k,
        device=device,
        batch_size=embedding_batch_size,
    )
    candidate_config = build_hybrid_experiment_config(
        chunks,
        retriever_name=candidate_retriever.name,
        sparse=sparse_config,
        dense=dense_config,
        candidate_k=fusion_candidate_k,
        rrf_k=rrf_k,
        sparse_weight=sparse_weight,
        dense_weight=dense_weight,
        seed=seed,
        top_k=top_k,
    )
    reranked_config = RerankedRetrievalExperimentConfig(
        seed=seed,
        top_k=top_k,
        retriever=reranked_retriever.name,
        corpus_chunk_count=len(chunks),
        candidate_k=rerank_candidate_k,
        candidate=candidate_config,
        reranker=reranker.name,
        model_id=reranking_spec.model_id,
        model_revision=reranking_spec.revision,
        max_sequence_length=reranking_spec.max_sequence_length,
        device=device,
        batch_size=reranking_batch_size,
    )
    return RerankingRuntime(
        embedding_spec=embedding_spec,
        reranking_spec=reranking_spec,
        tokenizer=tokenizer,
        candidate_retriever=candidate_retriever,
        reranked_retriever=reranked_retriever,
        candidate_config=candidate_config,
        reranked_config=reranked_config,
        candidate_setup_latency_ms=candidate_setup_latency_ms,
        setup_latency_ms=setup_latency_ms,
        truncated_document_count=truncated_document_count,
    )
