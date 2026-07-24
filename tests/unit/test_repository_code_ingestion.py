from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from rag_pymc.chunking import RepositoryCodeChunker
from rag_pymc.cli import app
from rag_pymc.domain import SourceManifest, SourceType
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.ingestion.errors import DocumentParseError
from rag_pymc.parsing import PythonRepositoryParser
from rag_pymc.persistence import JsonlDocumentRepository

SOURCE = b'''from typing import overload

@overload
def sample(draws: int) -> int: ...

def sample(draws: int = 1000) -> int:
    """Draw posterior samples.

    Additional documentation belongs to the API-reference corpus.
    """
    retained_draws = draws
    if retained_draws < 1:
        raise ValueError("draws must be positive")
    return retained_draws
'''
NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)
COMMIT = "56384e5afed6d1ad122e19b1bf3a7885fc38e5e5"


def make_manifest(**overrides: object) -> SourceManifest:
    values: dict[str, object] = {
        "source_id": "pymc-6.1.0-repository-code-pymc.sample",
        "library": "pymc",
        "library_version": "6.1.0",
        "source_type": SourceType.REPOSITORY_CODE,
        "source_url": ("https://github.com/pymc-devs/pymc/blob/v6.1.0/pymc/sampling/mcmc.py"),
        "release_tag": "v6.1.0",
        "release_url": "https://github.com/pymc-devs/pymc/releases/tag/v6.1.0",
        "source_commit": COMMIT,
        "downloaded_at": NOW,
        "content_hash": sha256(SOURCE).hexdigest(),
        "media_type": "text/x-python",
        "expected_api_symbol": "pymc.sample",
        "source_path": "pymc/sampling/mcmc.py",
        "license_name": "Apache-2.0",
        "license_url": "https://github.com/pymc-devs/pymc/blob/v6.1.0/LICENSE",
    }
    values.update(overrides)
    return SourceManifest.model_validate(values)


def test_repository_manifest_requires_symbol_commit_and_relative_path() -> None:
    with pytest.raises(ValidationError, match="expected_api_symbol"):
        make_manifest(expected_api_symbol=None)
    with pytest.raises(ValidationError, match="source_commit"):
        make_manifest(source_commit=None)
    with pytest.raises(ValidationError, match="source_path"):
        make_manifest(source_path=None)
    with pytest.raises(ValidationError, match="relative repository path"):
        make_manifest(source_path="../pymc/sampling/mcmc.py")


def test_python_repository_parser_selects_implementation_and_ast_blocks() -> None:
    parsed = PythonRepositoryParser().parse(SOURCE, make_manifest())

    assert parsed.api_symbol == "pymc.sample"
    assert parsed.source_path == "pymc/sampling/mcmc.py"
    assert parsed.signature == "def sample(draws: int = 1000) -> int:"
    assert parsed.docstring_summary == "Draw posterior samples."
    assert parsed.symbol_kind == "function"
    assert [block.content for block in parsed.blocks] == [
        "retained_draws = draws",
        'if retained_draws < 1:\n        raise ValueError("draws must be positive")',
        "return retained_draws",
    ]
    assert parsed.document.parser_version == "python-repository-ast-v1"
    assert parsed.document.source_type is SourceType.REPOSITORY_CODE


def test_python_repository_parser_rejects_wrong_source_contract() -> None:
    parser = PythonRepositoryParser()

    with pytest.raises(DocumentParseError, match="does not support"):
        parser.parse(
            SOURCE,
            make_manifest(source_type=SourceType.TUTORIAL),
        )
    with pytest.raises(DocumentParseError, match="not valid Python"):
        invalid_source = b"def invalid(:"
        parser.parse(
            invalid_source,
            make_manifest(content_hash=sha256(invalid_source).hexdigest()),
        )


def test_repository_chunker_is_deterministic_and_omits_duplicate_docstring_detail() -> None:
    parsed = PythonRepositoryParser().parse(SOURCE, make_manifest())
    chunker = RepositoryCodeChunker()

    first = chunker.chunk(parsed)
    second = chunker.chunk(parsed)

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert [chunk.section for chunk in first] == ["Definition", "Implementation 1"]
    assert all(chunk.api_symbols == ("pymc.sample",) for chunk in first)
    assert all(chunk.source_type is SourceType.REPOSITORY_CODE for chunk in first)
    assert all(chunk.chunker_version == "repository-code-ast-v1" for chunk in first)
    assert "Draw posterior samples." in first[0].content
    assert "Additional documentation" not in first[0].content
    assert "raise ValueError" in first[1].content


def test_repository_code_pipeline_and_cli_write_idempotent_corpus(tmp_path: Path) -> None:
    source_path = tmp_path / "mcmc.py"
    manifest_path = tmp_path / "manifest.json"
    output_dir = tmp_path / "corpus"
    source_path.write_bytes(SOURCE)
    manifest_path.write_text(make_manifest().model_dump_json(), encoding="utf-8")
    repository = JsonlDocumentRepository(output_dir)
    service = IngestionService(
        fetcher=LocalFileSourceFetcher(source_path),
        parser=PythonRepositoryParser(),
        chunker=RepositoryCodeChunker(),
        repository=repository,
    )

    first = service.run(make_manifest())
    second = service.run(make_manifest())

    assert first == second
    assert len(repository.load_documents()) == 1
    assert len(repository.load_chunks()) == 2

    cli_output = tmp_path / "cli-corpus"
    result = CliRunner().invoke(
        app,
        [
            "ingest-code",
            "--manifest",
            str(manifest_path),
            "--source",
            str(source_path),
            "--output-dir",
            str(cli_output),
        ],
    )

    assert result.exit_code == 0
    assert "rag-pymc ingest-code" in result.stdout
    assert "chunks: 2" in result.stdout
    assert len(JsonlDocumentRepository(cli_output).load_chunks()) == 2
