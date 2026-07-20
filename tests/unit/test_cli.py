from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from rag_pymc.cli import app
from rag_pymc.domain import Chunk
from rag_pymc.embeddings import EmbeddingMatrix, EmbeddingModelSpec
from rag_pymc.reranking import RerankingModelSpec

runner = CliRunner()


def test_doctor_reports_healthy_environment() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "rag-pymc doctor" in result.stdout
    assert "pymc:" in result.stdout
    assert "arviz:" in result.stdout
    assert "pytensor:" in result.stdout
    assert "status: ok" in result.stdout


def test_ingest_command_writes_local_corpus(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "corpus"

    result = runner.invoke(
        app,
        [
            "ingest",
            "--manifest",
            str(manifest_path),
            "--source",
            str(source_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "chunks: 5" in result.stdout


def test_search_and_evaluate_commands_use_ingested_corpus(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
) -> None:
    corpus_dir = tmp_path / "corpus"
    report_path = tmp_path / "report.json"
    dataset_path = (
        Path(__file__).resolve().parents[2] / "datasets/evaluation/phase2/pymc_sample_queries.jsonl"
    )
    ingest_result = runner.invoke(
        app,
        [
            "ingest",
            "--manifest",
            str(manifest_path),
            "--source",
            str(source_path),
            "--output-dir",
            str(corpus_dir),
        ],
    )
    search_result = runner.invoke(
        app,
        [
            "search",
            "What does pymc.sample do?",
            "--corpus-dir",
            str(corpus_dir),
            "--library",
            "pymc",
            "--library-version",
            "6.1.0",
        ],
    )
    evaluation_result = runner.invoke(
        app,
        [
            "evaluate",
            "--dataset",
            str(dataset_path),
            "--corpus-dir",
            str(corpus_dir),
            "--output",
            str(report_path),
        ],
    )

    assert ingest_result.exit_code == 0
    assert search_result.exit_code == 0
    assert "chunk_bdbac941d4ebd7c396ed" in search_result.stdout
    assert evaluation_result.exit_code == 0
    assert "queries: 20" in evaluation_result.stdout
    assert report_path.is_file()


class FakeCliEmbedder:
    name = "fake-cli-v1"

    def __init__(
        self,
        spec: EmbeddingModelSpec,
        *,
        device: str,
        batch_size: int,
        seed: int,
        local_files_only: bool,
    ) -> None:
        self.model_id = spec.model_id
        self.revision = spec.revision
        self.dimension = spec.dimension

    def embed_documents(self, texts: Sequence[str]) -> EmbeddingMatrix:
        matrix = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for index in range(len(texts)):
            matrix[index, index] = 1.0
        return matrix

    def token_count(self, text: str) -> int:
        return len(text.split())

    def embed_query(self, text: str) -> EmbeddingMatrix:
        matrix = np.zeros((1, self.dimension), dtype=np.float32)
        matrix[0, 0] = 1.0
        return matrix


def test_dense_cli_commands_write_reports_without_network(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    corpus_dir = tmp_path / "corpus"
    dense_report = tmp_path / "dense.json"
    comparison_report = tmp_path / "comparison.json"
    dataset_path = project_root / "datasets/evaluation/phase2/pymc_sample_queries.jsonl"
    model_manifest = project_root / "datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.SentenceTransformerEmbedder",
        FakeCliEmbedder,
    )
    ingest_result = runner.invoke(
        app,
        [
            "ingest",
            "--manifest",
            str(manifest_path),
            "--source",
            str(source_path),
            "--output-dir",
            str(corpus_dir),
        ],
    )
    search_result = runner.invoke(
        app,
        [
            "search-dense",
            "What does pymc.sample do?",
            "--corpus-dir",
            str(corpus_dir),
            "--model-manifest",
            str(model_manifest),
        ],
    )
    evaluation_result = runner.invoke(
        app,
        [
            "evaluate-dense",
            "--dataset",
            str(dataset_path),
            "--corpus-dir",
            str(corpus_dir),
            "--model-manifest",
            str(model_manifest),
            "--dense-output",
            str(dense_report),
            "--comparison-output",
            str(comparison_report),
        ],
    )

    assert ingest_result.exit_code == 0
    assert search_result.exit_code == 0
    assert "model: BAAI/bge-small-en-v1.5@" in search_result.stdout
    assert evaluation_result.exit_code == 0
    assert "queries: 20" in evaluation_result.stdout
    assert dense_report.is_file()
    assert comparison_report.is_file()


def test_hybrid_cli_writes_all_benchmark_artifacts_without_network(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    corpus_dir = tmp_path / "corpus"
    outputs = {
        name: tmp_path / f"{name}.json"
        for name in ("sparse", "dense", "hybrid", "bm25-comparison", "dense-comparison")
    }
    dataset_path = project_root / "datasets/evaluation/phase2/pymc_sample_queries.jsonl"
    model_manifest = project_root / "datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.SentenceTransformerEmbedder",
        FakeCliEmbedder,
    )
    ingest_result = runner.invoke(
        app,
        [
            "ingest",
            "--manifest",
            str(manifest_path),
            "--source",
            str(source_path),
            "--output-dir",
            str(corpus_dir),
        ],
    )
    search_result = runner.invoke(
        app,
        [
            "search-hybrid",
            "What does pymc.sample do?",
            "--corpus-dir",
            str(corpus_dir),
            "--model-manifest",
            str(model_manifest),
        ],
    )
    evaluation_result = runner.invoke(
        app,
        [
            "evaluate-hybrid",
            "--dataset",
            str(dataset_path),
            "--corpus-dir",
            str(corpus_dir),
            "--model-manifest",
            str(model_manifest),
            "--sparse-output",
            str(outputs["sparse"]),
            "--dense-output",
            str(outputs["dense"]),
            "--hybrid-output",
            str(outputs["hybrid"]),
            "--bm25-comparison-output",
            str(outputs["bm25-comparison"]),
            "--dense-comparison-output",
            str(outputs["dense-comparison"]),
        ],
    )

    assert ingest_result.exit_code == 0
    assert search_result.exit_code == 0
    assert "rag-pymc search-hybrid" in search_result.stdout
    assert evaluation_result.exit_code == 0
    assert "queries: 20" in evaluation_result.stdout
    assert all(path.is_file() for path in outputs.values())


class FakeCliReranker:
    name = "fake-cli-reranker-v1"

    def __init__(
        self,
        spec: RerankingModelSpec,
        *,
        device: str,
        batch_size: int,
        seed: int,
        local_files_only: bool,
    ) -> None:
        self.model_id = spec.model_id
        self.revision = spec.revision

    def score(self, query: str, chunks: Sequence[Chunk]) -> tuple[float, ...]:
        return tuple(float(len(chunks) - index) for index in range(len(chunks)))


def test_reranked_cli_writes_control_candidate_and_comparison_without_network(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    corpus_dir = tmp_path / "corpus"
    candidate_output = tmp_path / "candidate.json"
    reranked_output = tmp_path / "reranked.json"
    comparison_output = tmp_path / "comparison.json"
    dataset_path = project_root / "datasets/evaluation/phase2/pymc_sample_queries.jsonl"
    embedding_manifest = project_root / "datasets/raw/manifests/embeddings/bge-small-en-v1.5.json"
    reranker_manifest = project_root / "datasets/raw/manifests/rerankers/ms-marco-MiniLM-L6-v2.json"
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.SentenceTransformerEmbedder",
        FakeCliEmbedder,
    )
    monkeypatch.setattr(
        "rag_pymc.reranking.sentence_transformer.SentenceTransformerCrossEncoderReranker",
        FakeCliReranker,
    )
    ingest_result = runner.invoke(
        app,
        [
            "ingest",
            "--manifest",
            str(manifest_path),
            "--source",
            str(source_path),
            "--output-dir",
            str(corpus_dir),
        ],
    )
    search_result = runner.invoke(
        app,
        [
            "search-reranked",
            "What does pymc.sample do?",
            "--corpus-dir",
            str(corpus_dir),
            "--embedding-manifest",
            str(embedding_manifest),
            "--reranker-manifest",
            str(reranker_manifest),
        ],
    )
    evaluation_result = runner.invoke(
        app,
        [
            "evaluate-reranked",
            "--dataset",
            str(dataset_path),
            "--corpus-dir",
            str(corpus_dir),
            "--embedding-manifest",
            str(embedding_manifest),
            "--reranker-manifest",
            str(reranker_manifest),
            "--candidate-output",
            str(candidate_output),
            "--reranked-output",
            str(reranked_output),
            "--comparison-output",
            str(comparison_output),
        ],
    )

    assert ingest_result.exit_code == 0
    assert search_result.exit_code == 0
    assert "rag-pymc search-reranked" in search_result.stdout
    assert evaluation_result.exit_code == 0
    assert "queries: 20" in evaluation_result.stdout
    assert candidate_output.is_file()
    assert reranked_output.is_file()
    assert comparison_output.is_file()
