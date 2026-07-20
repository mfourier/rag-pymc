import json
from pathlib import Path

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import SourceManifest
from rag_pymc.evaluation import (
    RetrievalEvaluator,
    RetrievalExperimentConfig,
    load_evaluation_queries,
    write_experiment_report,
)
from rag_pymc.indexing import BM25Index
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonlDocumentRepository
from rag_pymc.retrieval import SparseRetriever, TechnicalTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "datasets/evaluation/phase2/pymc_sample_queries.jsonl"


def test_sparse_retrieval_evaluation_uses_real_ingested_chunks(
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
    known_chunk_ids = {chunk.chunk_id for chunk in chunks}
    judged_chunk_ids = {chunk_id for query in queries for chunk_id in query.relevant_chunk_ids}

    tokenizer = TechnicalTokenizer()
    index = BM25Index(chunks, tokenizer=tokenizer)
    config = RetrievalExperimentConfig(
        seed=20260719,
        top_k=3,
        retriever=index.name,
        tokenizer=tokenizer.name,
        k1=index.k1,
        b=index.b,
        corpus_chunk_count=len(chunks),
    )
    evaluator = RetrievalEvaluator(
        retriever=SparseRetriever(index),
        chunks=chunks,
        tokenizer=tokenizer,
        config=config,
    )
    report = evaluator.evaluate(queries, dataset_path=DATASET_PATH)
    report_path = tmp_path / "report.json"
    write_experiment_report(report, report_path)
    stored = json.loads(report_path.read_text(encoding="utf-8"))

    slices = {(item.dimension, item.value): item.metrics for item in report.slices}
    assert slices[("intent", "unanswerable")].query_count == 2
    assert slices[("intent", "unanswerable")].recall_at_k == 0.0
    assert slices[("difficulty", "beginner")].query_count == 8
    assert len(stored["slices"]) == len(report.slices)

    assert len(chunks) == 5
    assert len(queries) == 20
    assert judged_chunk_ids <= known_chunk_ids
    assert report.metrics.answerable_query_count == 18
    assert report.metrics.unanswerable_query_count == 2
    assert report.metrics.version_correctness == 1.0
    assert len(report.queries) == len(queries)
    assert stored["experiment_id"] == "phase2-bm25-baseline"
    assert stored["config"]["corpus_chunk_count"] == 5
