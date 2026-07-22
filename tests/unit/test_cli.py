from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import numpy as np
import pytest
from typer.testing import CliRunner

from rag_pymc.cli import app
from rag_pymc.domain import Chunk, ConstructedContext
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


class TrackingFakeCliEmbedder(FakeCliEmbedder):
    local_files_only_values: ClassVar[list[bool]] = []

    def __init__(
        self,
        spec: EmbeddingModelSpec,
        *,
        device: str,
        batch_size: int,
        seed: int,
        local_files_only: bool,
    ) -> None:
        super().__init__(
            spec,
            device=device,
            batch_size=batch_size,
            seed=seed,
            local_files_only=local_files_only,
        )
        self.local_files_only_values.append(local_files_only)


@pytest.fixture
def context_cli_corpus(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
) -> Path:
    corpus_dir = tmp_path / "context-corpus"
    result = runner.invoke(
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

    assert result.exit_code == 0
    return corpus_dir


def test_inspect_context_emits_deterministic_domain_json_offline(
    context_cli_corpus: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    TrackingFakeCliEmbedder.local_files_only_values.clear()
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.SentenceTransformerEmbedder",
        TrackingFakeCliEmbedder,
    )
    arguments = [
        "inspect-context",
        "What does pymc.sample do?",
        "--corpus-dir",
        str(context_cli_corpus),
        "--token-budget",
        "100000",
    ]

    first = runner.invoke(app, arguments)
    second = runner.invoke(app, arguments)
    download_enabled = runner.invoke(app, [*arguments, "--allow-download"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert download_enabled.exit_code == 0
    assert first.stdout == second.stdout
    assert download_enabled.stdout == first.stdout
    context = ConstructedContext.model_validate_json(first.stdout)
    assert context.query.library == "pymc"
    assert context.query.library_version == "6.1.0"
    assert context.query.top_k == 3
    assert context.token_counter == "technical-v1"
    assert context.token_budget == 100000
    assert len(context.items) == 3
    assert context.included_chunk_ids == tuple(item.chunk_id for item in context.items)
    assert context.omitted_chunk_ids == ()
    assert all(item.retriever == "weighted-rrf-v1" for item in context.items)
    assert all(str(item.source_url).startswith("https://www.pymc.io/") for item in context.items)
    assert TrackingFakeCliEmbedder.local_files_only_values == [True, True, False]


def test_inspect_context_accepts_exact_budget_and_omits_from_first_overflow(
    context_cli_corpus: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.SentenceTransformerEmbedder",
        FakeCliEmbedder,
    )
    common_arguments = [
        "inspect-context",
        "What does pymc.sample do?",
        "--corpus-dir",
        str(context_cli_corpus),
    ]
    full_result = runner.invoke(app, [*common_arguments, "--token-budget", "100000"])
    assert full_result.exit_code == 0
    full = ConstructedContext.model_validate_json(full_result.stdout)
    first_item_cost = full.items[0].token_count

    exact_result = runner.invoke(
        app,
        [*common_arguments, "--token-budget", str(first_item_cost)],
    )
    under_result = runner.invoke(
        app,
        [*common_arguments, "--token-budget", str(first_item_cost - 1)],
    )

    assert exact_result.exit_code == 0
    assert under_result.exit_code == 0
    exact = ConstructedContext.model_validate_json(exact_result.stdout)
    under = ConstructedContext.model_validate_json(under_result.stdout)
    assert exact.included_chunk_ids == full.included_chunk_ids[:1]
    assert exact.omitted_chunk_ids == full.included_chunk_ids[1:]
    assert exact.used_tokens == exact.token_budget
    assert under.included_chunk_ids == ()
    assert under.omitted_chunk_ids == full.included_chunk_ids
    assert under.used_tokens == 0


def test_inspect_context_treats_no_matches_as_a_valid_empty_context(
    context_cli_corpus: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "rag_pymc.embeddings.sentence_transformer.SentenceTransformerEmbedder",
        FakeCliEmbedder,
    )

    result = runner.invoke(
        app,
        [
            "inspect-context",
            "How do I summarize an InferenceData object?",
            "--corpus-dir",
            str(context_cli_corpus),
            "--token-budget",
            "1000",
            "--library",
            "arviz",
            "--library-version",
            "1.2.0",
        ],
    )

    assert result.exit_code == 0
    context = ConstructedContext.model_validate_json(result.stdout)
    assert context.query.library == "arviz"
    assert context.query.library_version == "1.2.0"
    assert context.items == ()
    assert context.included_chunk_ids == ()
    assert context.omitted_chunk_ids == ()
    assert context.used_tokens == 0


def test_inspect_context_reports_runtime_failures_without_partial_json(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "inspect-context",
            "What does pymc.sample do?",
            "--corpus-dir",
            str(tmp_path / "empty-corpus"),
            "--token-budget",
            "1000",
        ],
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "context inspection failed:" in result.stderr


def test_inspect_context_validates_query_before_loading_the_corpus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_load(_: object) -> tuple[Chunk, ...]:
        pytest.fail("corpus loading must not run for an invalid query")

    monkeypatch.setattr(
        "rag_pymc.cli.JsonlDocumentRepository.load_chunks",
        unexpected_load,
    )

    result = runner.invoke(
        app,
        ["inspect-context", "   ", "--token-budget", "100"],
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "context inspection failed:" in result.stderr


def test_inspect_context_help_describes_the_explicit_bounded_interface() -> None:
    result = runner.invoke(
        app,
        ["inspect-context", "--help"],
        env={"COLUMNS": "160"},
    )

    assert result.exit_code == 0
    assert "--token-budget" in result.stdout
    assert "--top-k" in result.stdout
    assert "--local-files-only" in result.stdout
    assert "--allow-download" in result.stdout


@pytest.mark.parametrize(
    "arguments",
    [
        ["inspect-context", "query"],
        ["inspect-context", "query", "--token-budget", "0"],
        ["inspect-context", "query", "--token-budget", "100", "--top-k", "11"],
    ],
)
def test_inspect_context_rejects_missing_or_out_of_range_arguments(
    arguments: list[str],
) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 2


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
