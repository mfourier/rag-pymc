from hashlib import sha256
from pathlib import Path

import pytest

from rag_pymc.chunking import RepositoryCodeChunker
from rag_pymc.domain import SourceManifest, SourceType
from rag_pymc.evaluation import load_evaluation_queries
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import PythonRepositoryParser
from rag_pymc.persistence import JsonlDocumentRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMMIT = "56384e5afed6d1ad122e19b1bf3a7885fc38e5e5"
CASES = (
    (
        "pymc.sample.json",
        "pymc/sampling/mcmc.py",
        "pymc.sample",
    ),
    (
        "pymc.Data.json",
        "pymc/data.py",
        "pymc.Data",
    ),
    (
        "pymc.model.core.set_data.json",
        "pymc/model/core.py",
        "pymc.model.core.set_data",
    ),
    (
        "pymc.sample_posterior_predictive.json",
        "pymc/sampling/forward.py",
        "pymc.sample_posterior_predictive",
    ),
)


def manifest_path(name: str) -> Path:
    return PROJECT_ROOT / "datasets/raw/manifests/pymc/6.1.0/repository" / name


def source_path(name: str) -> Path:
    return PROJECT_ROOT / "datasets/fixtures/pymc/6.1.0/repository" / name


@pytest.mark.parametrize(("manifest_name", "relative_source", "api_symbol"), CASES)
def test_repository_snapshot_matches_manifest_and_expected_symbol(
    manifest_name: str,
    relative_source: str,
    api_symbol: str,
) -> None:
    manifest = SourceManifest.model_validate_json(
        manifest_path(manifest_name).read_text(encoding="utf-8")
    )
    source = LocalFileSourceFetcher(source_path(relative_source)).fetch(manifest)
    parsed = PythonRepositoryParser().parse(source, manifest)
    chunks = RepositoryCodeChunker().chunk(parsed)

    assert sha256(source).hexdigest() == manifest.content_hash
    assert manifest.library_version == "6.1.0"
    assert manifest.source_commit == COMMIT
    assert manifest.source_path == relative_source
    assert manifest.expected_api_symbol == api_symbol
    assert parsed.api_symbol == api_symbol
    assert parsed.document.source_type is SourceType.REPOSITORY_CODE
    assert chunks[0].section == "Definition"
    assert all(chunk.api_symbols == (api_symbol,) for chunk in chunks)
    assert all(len(chunk.content) < 3_000 for chunk in chunks)


def test_repository_snapshots_build_one_idempotent_corpus(tmp_path: Path) -> None:
    repository = JsonlDocumentRepository(tmp_path / "corpus")
    observed_chunk_counts: dict[str, int] = {}

    for manifest_name, relative_source, api_symbol in CASES:
        manifest = SourceManifest.model_validate_json(
            manifest_path(manifest_name).read_text(encoding="utf-8")
        )
        service = IngestionService(
            fetcher=LocalFileSourceFetcher(source_path(relative_source)),
            parser=PythonRepositoryParser(),
            chunker=RepositoryCodeChunker(),
            repository=repository,
        )
        first = service.run(manifest)
        second = service.run(manifest)
        assert first == second
        observed_chunk_counts[api_symbol] = len(first.chunks)

    assert len(repository.load_documents()) == 4
    assert observed_chunk_counts == {
        "pymc.Data": 2,
        "pymc.model.core.set_data": 2,
        "pymc.sample": 8,
        "pymc.sample_posterior_predictive": 7,
    }
    assert len(repository.load_chunks()) == 19


def test_repository_code_evaluation_qrels_resolve_to_built_corpus(tmp_path: Path) -> None:
    repository = JsonlDocumentRepository(tmp_path / "corpus")
    for manifest_name, relative_source, _ in CASES:
        manifest = SourceManifest.model_validate_json(
            manifest_path(manifest_name).read_text(encoding="utf-8")
        )
        IngestionService(
            fetcher=LocalFileSourceFetcher(source_path(relative_source)),
            parser=PythonRepositoryParser(),
            chunker=RepositoryCodeChunker(),
            repository=repository,
        ).run(manifest)

    queries = load_evaluation_queries(
        PROJECT_ROOT / "datasets/evaluation/repository-code/pymc_implementation_queries.jsonl"
    )
    document_ids = {document.document_id for document in repository.load_documents()}
    chunk_ids = {chunk.chunk_id for chunk in repository.load_chunks()}

    assert len(queries) == 8
    assert all(query.source_types == (SourceType.REPOSITORY_CODE,) for query in queries)
    assert all(set(query.relevant_document_ids) <= document_ids for query in queries)
    assert all(set(query.relevant_chunk_ids) <= chunk_ids for query in queries)
