from collections.abc import Sequence
from pathlib import Path

import numpy as np

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import SourceManifest
from rag_pymc.embeddings import EmbeddingMatrix
from rag_pymc.evaluation import (
    DenseRetrievalExperimentConfig,
    RetrievalEvaluator,
    load_evaluation_queries,
)
from rag_pymc.indexing import ExactCosineIndex
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonlDocumentRepository
from rag_pymc.retrieval import DenseRetriever, TechnicalTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "datasets/evaluation/phase2/pymc_sample_queries.jsonl"


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


def test_dense_evaluation_runs_over_real_phase2_corpus(
    source_manifest: SourceManifest,
    source_path: Path,
    tmp_path: Path,
) -> None:
    repository = JsonlDocumentRepository(tmp_path / "corpus")
    ingestion = IngestionService(
        fetcher=LocalFileSourceFetcher(source_path),
        parser=SphinxApiParser(),
        chunker=ApiReferenceChunker(),
        repository=repository,
    )
    ingestion.run(source_manifest)
    chunks = repository.load_chunks()
    queries = load_evaluation_queries(DATASET_PATH)
    dimension = len(chunks)
    vectors_by_chunk_id = {
        chunk.chunk_id: np.eye(dimension, dtype=np.float32)[index : index + 1]
        for index, chunk in enumerate(chunks)
    }
    embedder = QrelEmbedder(
        document_vectors={chunk.content: vectors_by_chunk_id[chunk.chunk_id] for chunk in chunks},
        query_vectors={
            query.question: (
                vectors_by_chunk_id[query.relevant_chunk_ids[0]]
                if query.answerable
                else np.ones((1, dimension), dtype=np.float32)
            )
            for query in queries
        },
        dimension=dimension,
    )
    index = ExactCosineIndex(chunks, embedder=embedder)
    config = DenseRetrievalExperimentConfig(
        seed=20260719,
        top_k=3,
        retriever=index.name,
        corpus_chunk_count=len(chunks),
        embedder=embedder.name,
        model_id=embedder.model_id,
        model_revision=embedder.revision,
        dimension=dimension,
        normalize_embeddings=True,
        max_sequence_length=512,
        truncated_document_count=0,
        device="cpu",
        batch_size=20,
    )

    report = RetrievalEvaluator(
        retriever=DenseRetriever(index),
        chunks=chunks,
        tokenizer=TechnicalTokenizer(),
        config=config,
        experiment_id="test-dense",
    ).evaluate(queries, dataset_path=DATASET_PATH)

    assert report.metrics.query_count == 20
    assert report.metrics.recall_at_k == 1.0
    assert report.metrics.hit_rate_at_k == 1.0
    assert report.metrics.version_correctness == 1.0
    assert report.config == config
