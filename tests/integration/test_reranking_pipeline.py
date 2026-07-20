from collections.abc import Sequence
from pathlib import Path

import numpy as np

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import Chunk, SourceManifest
from rag_pymc.embeddings import EmbeddingMatrix
from rag_pymc.evaluation import (
    DenseRetrievalExperimentConfig,
    HybridRetrievalExperimentConfig,
    RerankedRetrievalExperimentConfig,
    RetrievalEvaluator,
    RetrievalExperimentConfig,
    load_evaluation_queries,
)
from rag_pymc.indexing import BM25Index, ExactCosineIndex
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonlDocumentRepository
from rag_pymc.reranking import RerankedRetriever
from rag_pymc.retrieval import (
    DenseRetriever,
    ReciprocalRankFusionRetriever,
    SparseRetriever,
    TechnicalTokenizer,
    WeightedRetriever,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "datasets/evaluation/phase4/pymc_core_queries.jsonl"
SOURCE_NAMES = (
    "pymc.sample",
    "pymc.Data",
    "pymc.model.core.set_data",
    "pymc.sample_posterior_predictive",
)


class QueryEmbedder:
    name = "query-fake-v1"
    model_id = "test/query"
    revision = "a" * 40

    def __init__(
        self,
        chunks: Sequence[Chunk],
        query_targets: dict[str, str | None],
    ) -> None:
        self.dimension = len(chunks)
        self._vectors = {
            chunk.chunk_id: np.eye(self.dimension, dtype=np.float32)[index : index + 1]
            for index, chunk in enumerate(chunks)
        }
        self._content_ids = {chunk.content: chunk.chunk_id for chunk in chunks}
        self._query_targets = query_targets

    def embed_documents(self, texts: Sequence[str]) -> EmbeddingMatrix:
        return np.vstack([self._vectors[self._content_ids[text]] for text in texts])

    def embed_query(self, text: str) -> EmbeddingMatrix:
        target = self._query_targets[text]
        if target is None:
            return np.ones((1, self.dimension), dtype=np.float32)
        return self._vectors[target]


class QrelReranker:
    name = "qrel-reranker-v1"
    model_id = "test/qrel"
    revision = "b" * 40

    def __init__(self, qrels: dict[str, set[str]]) -> None:
        self._qrels = qrels

    def score(self, query: str, chunks: Sequence[Chunk]) -> tuple[float, ...]:
        relevant = self._qrels[query]
        return tuple(1.0 if chunk.chunk_id in relevant else 0.0 for chunk in chunks)


def test_reranked_evaluation_runs_over_hybrid_candidates(tmp_path: Path) -> None:
    repository = JsonlDocumentRepository(tmp_path / "corpus")
    for source_name in SOURCE_NAMES:
        manifest_path = PROJECT_ROOT / f"datasets/raw/manifests/pymc/6.1.0/{source_name}.json"
        source_path = PROJECT_ROOT / f"datasets/fixtures/pymc/6.1.0/{source_name}.html"
        manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        IngestionService(
            fetcher=LocalFileSourceFetcher(source_path),
            parser=SphinxApiParser(),
            chunker=ApiReferenceChunker(),
            repository=repository,
        ).run(manifest)

    chunks = repository.load_chunks()
    queries = load_evaluation_queries(DATASET_PATH)
    embedder = QueryEmbedder(
        chunks,
        {
            query.question: query.relevant_chunk_ids[0] if query.answerable else None
            for query in queries
        },
    )
    tokenizer = TechnicalTokenizer()
    sparse_index = BM25Index(chunks, tokenizer=tokenizer)
    dense_index = ExactCosineIndex(chunks, embedder=embedder)
    sparse_config = RetrievalExperimentConfig(
        seed=20260720,
        top_k=3,
        retriever=sparse_index.name,
        tokenizer=tokenizer.name,
        k1=sparse_index.k1,
        b=sparse_index.b,
        corpus_chunk_count=len(chunks),
    )
    dense_config = DenseRetrievalExperimentConfig(
        seed=20260720,
        top_k=3,
        retriever=dense_index.name,
        corpus_chunk_count=len(chunks),
        embedder=embedder.name,
        model_id=embedder.model_id,
        model_revision=embedder.revision,
        dimension=embedder.dimension,
        normalize_embeddings=True,
        max_sequence_length=512,
        truncated_document_count=0,
        device="cpu",
        batch_size=16,
    )
    hybrid = ReciprocalRankFusionRetriever(
        (
            WeightedRetriever("sparse", SparseRetriever(sparse_index)),
            WeightedRetriever("dense", DenseRetriever(dense_index)),
        ),
        rrf_k=60,
        candidate_k=15,
    )
    hybrid_config = HybridRetrievalExperimentConfig(
        seed=20260720,
        top_k=3,
        retriever=hybrid.name,
        corpus_chunk_count=len(chunks),
        candidate_k=15,
        rrf_k=60,
        sparse_weight=1.0,
        dense_weight=1.0,
        sparse=sparse_config,
        dense=dense_config,
    )
    reranker = QrelReranker({query.question: set(query.relevant_chunk_ids) for query in queries})
    retriever = RerankedRetriever(hybrid, reranker, candidate_k=15)
    config = RerankedRetrievalExperimentConfig(
        seed=20260720,
        top_k=3,
        retriever=retriever.name,
        corpus_chunk_count=len(chunks),
        candidate_k=15,
        candidate=hybrid_config,
        reranker=reranker.name,
        model_id=reranker.model_id,
        model_revision=reranker.revision,
        max_sequence_length=512,
        device="cpu",
        batch_size=16,
    )

    report = RetrievalEvaluator(
        retriever=retriever,
        chunks=chunks,
        tokenizer=tokenizer,
        config=config,
        experiment_id="test-reranked",
    ).evaluate(queries, dataset_path=DATASET_PATH)

    assert report.metrics.answerable_query_count == 27
    assert report.metrics.recall_at_k == 1.0
    assert report.metrics.hit_rate_at_k == 1.0
    assert report.metrics.correct_abstention_rate == 2 / 3
    assert report.metrics.version_correctness == 1.0
