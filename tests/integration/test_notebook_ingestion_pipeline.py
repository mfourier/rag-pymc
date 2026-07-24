from hashlib import sha256
from pathlib import Path

import pytest

from rag_pymc.chunking import NotebookChunker
from rag_pymc.domain import SourceManifest, SourceType
from rag_pymc.evaluation import load_evaluation_queries
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import NotebookParser
from rag_pymc.persistence import JsonlDocumentRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMMIT = "56384e5afed6d1ad122e19b1bf3a7885fc38e5e5"
SOURCE_ROOT = "docs/source/learn/core_notebooks"
CASES = (
    (
        "dimensionality.json",
        f"{SOURCE_ROOT}/dimensionality.ipynb",
        "Distribution Dimensionality",
        13,
    ),
    (
        "pymc_pytensor.json",
        f"{SOURCE_ROOT}/pymc_pytensor.ipynb",
        "PyMC and PyTensor",
        13,
    ),
    (
        "model_comparison.json",
        f"{SOURCE_ROOT}/model_comparison.ipynb",
        "Model comparison",
        8,
    ),
)


def manifest_path(name: str) -> Path:
    return PROJECT_ROOT / "datasets/raw/manifests/pymc/6.1.0/notebooks" / name


def source_path(name: str) -> Path:
    return PROJECT_ROOT / "datasets/fixtures/pymc/6.1.0/notebooks" / name


@pytest.mark.parametrize(
    ("manifest_name", "relative_source", "title", "chunk_count"),
    CASES,
)
def test_notebook_snapshot_matches_manifest_and_normalizes_inputs(
    manifest_name: str,
    relative_source: str,
    title: str,
    chunk_count: int,
) -> None:
    manifest = SourceManifest.model_validate_json(
        manifest_path(manifest_name).read_text(encoding="utf-8")
    )
    source = LocalFileSourceFetcher(source_path(relative_source)).fetch(manifest)
    parsed = NotebookParser().parse(source, manifest)
    chunks = NotebookChunker().chunk(parsed)

    assert sha256(source).hexdigest() == manifest.content_hash
    assert manifest.library_version == "6.1.0"
    assert manifest.source_commit == COMMIT
    assert manifest.source_path == relative_source
    assert parsed.title == title
    assert parsed.document.source_type is SourceType.NOTEBOOK
    assert parsed.document.parser_version == "jupyter-notebook-inputs-v1"
    assert len(chunks) == chunk_count
    assert all(chunk.chunker_version == "notebook-cells-v1" for chunk in chunks)
    assert all(len(chunk.content) < 3_500 for chunk in chunks)
    assert '"outputs"' not in parsed.document.content
    assert '"execution_count"' not in parsed.document.content


def test_notebook_snapshots_build_one_idempotent_corpus(tmp_path: Path) -> None:
    repository = JsonlDocumentRepository(tmp_path / "corpus")
    observed_chunk_counts: dict[str, int] = {}

    for manifest_name, relative_source, title, _ in CASES:
        manifest = SourceManifest.model_validate_json(
            manifest_path(manifest_name).read_text(encoding="utf-8")
        )
        service = IngestionService(
            fetcher=LocalFileSourceFetcher(source_path(relative_source)),
            parser=NotebookParser(),
            chunker=NotebookChunker(),
            repository=repository,
        )
        first = service.run(manifest)
        second = service.run(manifest)
        assert first == second
        observed_chunk_counts[title] = len(first.chunks)

    assert len(repository.load_documents()) == 3
    assert observed_chunk_counts == {
        "Distribution Dimensionality": 13,
        "Model comparison": 8,
        "PyMC and PyTensor": 13,
    }
    assert len(repository.load_chunks()) == 34


def test_notebook_evaluation_qrels_resolve_to_built_corpus(tmp_path: Path) -> None:
    repository = JsonlDocumentRepository(tmp_path / "corpus")
    for manifest_name, relative_source, _, _ in CASES:
        manifest = SourceManifest.model_validate_json(
            manifest_path(manifest_name).read_text(encoding="utf-8")
        )
        IngestionService(
            fetcher=LocalFileSourceFetcher(source_path(relative_source)),
            parser=NotebookParser(),
            chunker=NotebookChunker(),
            repository=repository,
        ).run(manifest)

    queries = load_evaluation_queries(
        PROJECT_ROOT / "datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl"
    )
    document_ids = {document.document_id for document in repository.load_documents()}
    chunk_ids = {chunk.chunk_id for chunk in repository.load_chunks()}

    assert len(queries) == 10
    assert all(query.source_types == (SourceType.NOTEBOOK,) for query in queries)
    assert all(set(query.relevant_document_ids) <= document_ids for query in queries)
    assert all(set(query.relevant_chunk_ids) <= chunk_ids for query in queries)
