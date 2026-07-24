from pathlib import Path

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import SourceManifest
from rag_pymc.evaluation import (
    Phase5AnnotationCorpusFreeze,
    build_phase5_annotation_corpus_freeze,
)
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


def test_frozen_phase5_annotation_corpus_rebuilds_from_controlled_sources(
    tmp_path: Path,
) -> None:
    repository = JsonlDocumentRepository(tmp_path / "corpus")
    for source_name in SOURCE_NAMES:
        manifest_path = PROJECT_ROOT / f"datasets/raw/manifests/pymc/6.1.0/{source_name}.json"
        source_path = PROJECT_ROOT / f"datasets/fixtures/pymc/6.1.0/{source_name}.html"
        manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        service = IngestionService(
            fetcher=LocalFileSourceFetcher(source_path),
            parser=SphinxApiParser(),
            chunker=ApiReferenceChunker(),
            repository=repository,
        )
        service.run(manifest)

    report_path = PROJECT_ROOT / "reports/evaluation/phase5-annotation-corpus-freeze-v1.json"
    recorded = Phase5AnnotationCorpusFreeze.model_validate_json(
        report_path.read_text(encoding="utf-8")
    )
    rebuilt = build_phase5_annotation_corpus_freeze(
        repository.load_documents(),
        repository.load_chunks(),
        annotation_namespace=recorded.annotation_namespace,
        corpus_path=recorded.corpus_path,
        library=recorded.library,
        library_version=recorded.library_version,
        source_types=recorded.source_types,
        limitations=recorded.limitations,
    )

    assert rebuilt == recorded
