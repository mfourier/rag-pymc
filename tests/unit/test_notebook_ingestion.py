import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from rag_pymc.chunking import NotebookChunker
from rag_pymc.cli import app
from rag_pymc.domain import SourceManifest, SourceType
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.ingestion.errors import DocumentParseError
from rag_pymc.parsing import NotebookParser
from rag_pymc.persistence import JsonlDocumentRepository

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
COMMIT = "56384e5afed6d1ad122e19b1bf3a7885fc38e5e5"


def notebook_bytes(*, output_value: str = "ignored output") -> bytes:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"tags": ["remove-me"]},
                "source": ["(example)=\n", "# Notebook Title\n", "Introductory text."],
            },
            {
                "cell_type": "code",
                "execution_count": 12,
                "metadata": {"execution": {"iopub.status.busy": "timestamp"}},
                "outputs": [{"output_type": "stream", "text": [output_value]}],
                "source": ["with pm.Model() as model:\n", "    idata = pm.sample()"],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": "## Prediction\nGenerate predictive samples.",
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": "pm.sample_posterior_predictive(idata)",
            },
            {
                "cell_type": "raw",
                "metadata": {},
                "source": "Ignored raw cell",
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "volatile": "ignored notebook metadata",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(notebook).encode()


def make_manifest(source: bytes, **overrides: object) -> SourceManifest:
    values: dict[str, object] = {
        "source_id": "pymc-6.1.0-notebook-example",
        "library": "pymc",
        "library_version": "6.1.0",
        "source_type": SourceType.NOTEBOOK,
        "source_url": (
            "https://github.com/pymc-devs/pymc/blob/v6.1.0/"
            "docs/source/learn/core_notebooks/example.ipynb"
        ),
        "release_tag": "v6.1.0",
        "release_url": "https://github.com/pymc-devs/pymc/releases/tag/v6.1.0",
        "source_commit": COMMIT,
        "downloaded_at": NOW,
        "content_hash": sha256(source).hexdigest(),
        "media_type": "application/x-ipynb+json",
        "source_path": "docs/source/learn/core_notebooks/example.ipynb",
        "license_name": "Apache-2.0",
        "license_url": "https://github.com/pymc-devs/pymc/blob/v6.1.0/LICENSE",
    }
    values.update(overrides)
    return SourceManifest.model_validate(values)


def test_notebook_manifest_requires_commit_and_relative_source_path() -> None:
    source = notebook_bytes()

    with pytest.raises(ValidationError, match="source_commit"):
        make_manifest(source, source_commit=None)
    with pytest.raises(ValidationError, match="source_path"):
        make_manifest(source, source_path=None)
    with pytest.raises(ValidationError, match="relative repository path"):
        make_manifest(source, source_path="../example.ipynb")


def test_notebook_parser_ignores_outputs_metadata_and_raw_cells() -> None:
    source = notebook_bytes()
    parsed = NotebookParser().parse(source, make_manifest(source))

    assert parsed.title == "Notebook Title"
    assert [cell.cell_number for cell in parsed.cells] == [1, 2, 3, 4]
    assert [cell.section for cell in parsed.cells] == [
        "Notebook Title",
        "Notebook Title",
        "Notebook Title > Prediction",
        "Notebook Title > Prediction",
    ]
    assert parsed.cells[1].api_symbols == ("pymc.Model", "pymc.sample")
    assert parsed.cells[3].api_symbols == ("pymc.sample_posterior_predictive",)
    assert "ignored output" not in parsed.document.content
    assert "execution_count" not in parsed.document.content
    assert "Ignored raw cell" not in parsed.document.content
    assert parsed.document.parser_version == "jupyter-notebook-inputs-v1"

    changed_output = notebook_bytes(output_value="different ignored output")
    changed = NotebookParser().parse(changed_output, make_manifest(changed_output))
    assert changed.document == parsed.document
    assert changed.cells == parsed.cells


def test_notebook_parser_rejects_invalid_source_contracts() -> None:
    source = notebook_bytes()
    parser = NotebookParser()

    with pytest.raises(DocumentParseError, match="does not support"):
        parser.parse(source, make_manifest(source, source_type=SourceType.TUTORIAL))
    invalid_json = b"not-json"
    with pytest.raises(DocumentParseError, match="not valid UTF-8 JSON"):
        parser.parse(invalid_json, make_manifest(invalid_json))


def test_notebook_chunker_preserves_sections_cells_and_symbols() -> None:
    source = notebook_bytes()
    parsed = NotebookParser().parse(source, make_manifest(source))
    chunker = NotebookChunker()

    first = chunker.chunk(parsed)
    second = chunker.chunk(parsed)

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert [chunk.section for chunk in first] == [
        "Notebook Title",
        "Notebook Title > Prediction",
    ]
    assert first[0].api_symbols == ("pymc.Model", "pymc.sample")
    assert first[1].api_symbols == ("pymc.sample_posterior_predictive",)
    assert all(chunk.source_type is SourceType.NOTEBOOK for chunk in first)
    assert all(chunk.chunker_version == "notebook-cells-v1" for chunk in first)
    assert "Cell 2 [code]\n```python" in first[0].content


def test_notebook_pipeline_and_cli_write_idempotent_corpus(tmp_path: Path) -> None:
    source = notebook_bytes()
    manifest = make_manifest(source)
    source_path = tmp_path / "example.ipynb"
    manifest_path = tmp_path / "manifest.json"
    output_dir = tmp_path / "corpus"
    source_path.write_bytes(source)
    manifest_path.write_text(manifest.model_dump_json(), encoding="utf-8")
    repository = JsonlDocumentRepository(output_dir)
    service = IngestionService(
        fetcher=LocalFileSourceFetcher(source_path),
        parser=NotebookParser(),
        chunker=NotebookChunker(),
        repository=repository,
    )

    first = service.run(manifest)
    second = service.run(manifest)

    assert first == second
    assert len(repository.load_documents()) == 1
    assert len(repository.load_chunks()) == 2

    cli_output = tmp_path / "cli-corpus"
    result = CliRunner().invoke(
        app,
        [
            "ingest-notebook",
            "--manifest",
            str(manifest_path),
            "--source",
            str(source_path),
            "--output-dir",
            str(cli_output),
        ],
    )

    assert result.exit_code == 0
    assert "rag-pymc ingest-notebook" in result.stdout
    assert "chunks: 2" in result.stdout
    assert len(JsonlDocumentRepository(cli_output).load_chunks()) == 2
