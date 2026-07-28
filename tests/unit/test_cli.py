from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, cast

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from rag_pymc.cli import app
from rag_pymc.domain import Chunk, ConstructedContext

runner = CliRunner()


class _CommandGroup(Protocol):
    commands: Mapping[str, object]


def test_product_cli_exposes_only_the_selected_mvp_workflows() -> None:
    command = cast(_CommandGroup, get_command(app))

    assert set(command.commands) == {
        "doctor",
        "ingest",
        "search",
        "inspect-context",
        "evaluate",
    }


def test_doctor_reports_healthy_environment() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "rag-pymc doctor" in result.stdout
    assert "pymc:" in result.stdout
    assert "arviz:" in result.stdout
    assert "pytensor:" in result.stdout
    assert "status: ok" in result.stdout


@pytest.fixture
def cli_corpus(
    manifest_path: Path,
    source_path: Path,
    tmp_path: Path,
) -> Path:
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
    return output_dir


def test_search_and_evaluate_use_the_ingested_bm25_corpus(
    cli_corpus: Path,
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "report.json"
    dataset_path = project_root / "datasets/evaluation/phase2/pymc_sample_queries.jsonl"

    search_result = runner.invoke(
        app,
        [
            "search",
            "What does pymc.sample do?",
            "--corpus-dir",
            str(cli_corpus),
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
            str(cli_corpus),
            "--output",
            str(report_path),
        ],
    )

    assert search_result.exit_code == 0
    assert "chunk_bdbac941d4ebd7c396ed" in search_result.stdout
    assert evaluation_result.exit_code == 0
    assert "queries: 20" in evaluation_result.stdout
    assert report_path.is_file()


def test_inspect_context_emits_deterministic_bm25_domain_json(cli_corpus: Path) -> None:
    arguments = [
        "inspect-context",
        "What does pymc.sample do?",
        "--corpus-dir",
        str(cli_corpus),
        "--token-budget",
        "100000",
    ]

    first = runner.invoke(app, arguments)
    second = runner.invoke(app, arguments)

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.stdout == second.stdout
    context = ConstructedContext.model_validate_json(first.stdout)
    assert context.query.library == "pymc"
    assert context.query.library_version == "6.1.0"
    assert context.query.top_k == 3
    assert context.token_counter == "technical-v1"
    assert len(context.items) == 3
    assert all(item.retriever == "bm25-v1" for item in context.items)


def test_inspect_context_applies_exact_whole_item_budget(cli_corpus: Path) -> None:
    common = [
        "inspect-context",
        "What does pymc.sample do?",
        "--corpus-dir",
        str(cli_corpus),
    ]
    full_result = runner.invoke(app, [*common, "--token-budget", "100000"])
    assert full_result.exit_code == 0
    full = ConstructedContext.model_validate_json(full_result.stdout)
    first_item_cost = full.items[0].token_count

    exact_result = runner.invoke(app, [*common, "--token-budget", str(first_item_cost)])
    under_result = runner.invoke(app, [*common, "--token-budget", str(first_item_cost - 1)])

    exact = ConstructedContext.model_validate_json(exact_result.stdout)
    under = ConstructedContext.model_validate_json(under_result.stdout)
    assert exact.included_chunk_ids == full.included_chunk_ids[:1]
    assert exact.omitted_chunk_ids == full.included_chunk_ids[1:]
    assert exact.used_tokens == exact.token_budget
    assert under.included_chunk_ids == ()
    assert under.omitted_chunk_ids == full.included_chunk_ids


def test_inspect_context_treats_no_matches_as_valid_empty_context(cli_corpus: Path) -> None:
    result = runner.invoke(
        app,
        [
            "inspect-context",
            "How do I summarize an InferenceData object?",
            "--corpus-dir",
            str(cli_corpus),
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
    assert context.items == ()
    assert context.included_chunk_ids == ()
    assert context.omitted_chunk_ids == ()


def test_inspect_context_reports_failures_without_partial_json(tmp_path: Path) -> None:
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


def test_inspect_context_validates_query_before_loading_corpus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_load(_: object) -> tuple[Chunk, ...]:
        pytest.fail("corpus loading must not run for an invalid query")

    monkeypatch.setattr(
        "rag_pymc.cli.JsonlDocumentRepository.load_chunks",
        unexpected_load,
    )

    result = runner.invoke(app, ["inspect-context", "   ", "--token-budget", "100"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "context inspection failed:" in result.stderr


def test_inspect_context_help_exposes_only_the_bounded_sparse_interface() -> None:
    result = runner.invoke(app, ["inspect-context", "--help"], env={"COLUMNS": "160"})

    assert result.exit_code == 0
    assert "--token-budget" in result.stdout
    assert "--top-k" in result.stdout
    assert "--allow-download" not in result.stdout


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
