from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import SourceManifest
from rag_pymc.embeddings import EmbeddingMatrix
from rag_pymc.evaluation import (
    DenseRetrievalExperimentConfig,
    HybridRetrievalExperimentConfig,
    RetrievalEvaluator,
    RetrievalExperimentConfig,
    load_evaluation_queries,
)
from rag_pymc.indexing import BM25Index, ExactCosineIndex
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonlDocumentRepository
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


class QrelEmbedder:
    name = "qrel-fake-v1"
    model_id = "test/qrel"
    revision = "a" * 40

    def __init__(
        self,
        document_vectors: dict[str, EmbeddingMatrix],
        query_vectors: dict[str, EmbeddingMatrix],
        dimension: int,
    ) -> None:
        self._document_vectors = document_vectors
        self._query_vectors = query_vectors
        self.dimension = dimension

    def embed_documents(self, texts: Sequence[str]) -> EmbeddingMatrix:
        return np.vstack([self._document_vectors[text] for text in texts])

    def embed_query(self, text: str) -> EmbeddingMatrix:
        return self._query_vectors[text]


def test_hybrid_evaluation_runs_over_expanded_phase4_corpus(tmp_path: Path) -> None:
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
    dimension = len(chunks)
    vectors = {
        chunk.chunk_id: np.eye(dimension, dtype=np.float32)[index : index + 1]
        for index, chunk in enumerate(chunks)
    }
    embedder = QrelEmbedder(
        document_vectors={chunk.content: vectors[chunk.chunk_id] for chunk in chunks},
        query_vectors={
            query.question: (
                vectors[query.relevant_chunk_ids[0]]
                if query.answerable
                else np.ones((1, dimension), dtype=np.float32)
            )
            for query in queries
        },
        dimension=dimension,
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
        dimension=dimension,
        normalize_embeddings=True,
        max_sequence_length=512,
        truncated_document_count=0,
        device="cpu",
        batch_size=16,
    )
    retriever = ReciprocalRankFusionRetriever(
        (
            WeightedRetriever("sparse", SparseRetriever(sparse_index), 1.0),
            WeightedRetriever("dense", DenseRetriever(dense_index), 100.0),
        ),
        rrf_k=60,
        candidate_k=10,
    )
    config = HybridRetrievalExperimentConfig(
        seed=20260720,
        top_k=3,
        retriever=retriever.name,
        corpus_chunk_count=len(chunks),
        candidate_k=10,
        rrf_k=60,
        sparse_weight=1.0,
        dense_weight=100.0,
        sparse=sparse_config,
        dense=dense_config,
    )

    report = RetrievalEvaluator(
        retriever=retriever,
        chunks=chunks,
        tokenizer=tokenizer,
        config=config,
        experiment_id="test-hybrid",
    ).evaluate(queries, dataset_path=DATASET_PATH)

    judged_ids = {chunk_id for query in queries for chunk_id in query.relevant_chunk_ids}
    assert len(repository.load_documents()) == 4
    assert len(chunks) == 15
    assert len(queries) == 30
    assert judged_ids <= {chunk.chunk_id for chunk in chunks}
    assert report.metrics.answerable_query_count == 27
    assert report.metrics.unanswerable_query_count == 3
    assert report.metrics.hit_rate_at_k == 1.0
    assert report.metrics.recall_at_k == pytest.approx(26 / 27)
    assert report.metrics.version_correctness == 1.0
    assert {item.dimension for item in report.slices} == {"intent", "difficulty"}
