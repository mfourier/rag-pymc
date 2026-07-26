from pathlib import Path

import pytest
from typer.testing import CliRunner

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.cli import app
from rag_pymc.domain import SourceManifest
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonlDocumentRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAMES = (
    "pymc.sample",
    "pymc.Data",
    "pymc.model.core.set_data",
    "pymc.sample_posterior_predictive",
)
PRIOR_DATASETS = (
    "datasets/evaluation/phase2/pymc_sample_queries.jsonl",
    "datasets/evaluation/phase4/pymc_core_queries.jsonl",
    "datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl",
    "datasets/evaluation/repository-code/pymc_implementation_queries.jsonl",
)


def test_phase5_candidate_review_rebuilds_from_candidates_and_frozen_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corpus_dir = tmp_path / "corpus"
    repository = JsonlDocumentRepository(corpus_dir)
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

    output_path = tmp_path / "review.md"
    arguments = [
        "export-development-review",
        "--candidates",
        "datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl",
        "--corpus-dir",
        str(corpus_dir),
    ]
    for dataset in PRIOR_DATASETS:
        arguments.extend(("--prior-dataset", dataset))
    arguments.extend(("--output", str(output_path)))
    monkeypatch.chdir(PROJECT_ROOT)

    result = CliRunner().invoke(app, arguments)

    assert result.exit_code == 0
    assert result.stderr == ""
    assert "queries: 24" in result.stdout
    recorded_path = PROJECT_ROOT / "reports/evaluation/phase5-development-batch-v1-review.md"
    assert output_path.read_bytes() == recorded_path.read_bytes()
