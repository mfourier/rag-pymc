from pathlib import Path

import pytest

from rag_pymc.domain import SourceManifest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYMC_MANIFEST_PATH = PROJECT_ROOT / "datasets/raw/manifests/pymc/6.1.0/pymc.sample.json"
PYMC_SOURCE_PATH = PROJECT_ROOT / "datasets/fixtures/pymc/6.1.0/pymc.sample.html"


@pytest.fixture
def manifest_path() -> Path:
    return PYMC_MANIFEST_PATH


@pytest.fixture
def source_path() -> Path:
    return PYMC_SOURCE_PATH


@pytest.fixture
def source_manifest(manifest_path: Path) -> SourceManifest:
    return SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
