from hashlib import sha256
from pathlib import Path

import pytest

from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import SourceManifest
from rag_pymc.ingestion.errors import DocumentParseError, SourceIntegrityError
from rag_pymc.ingestion.fetchers import LocalFileSourceFetcher
from rag_pymc.parsing import SphinxApiParser


def test_source_fixture_matches_manifest(
    source_manifest: SourceManifest,
    source_path: Path,
) -> None:
    source = LocalFileSourceFetcher(source_path).fetch(source_manifest)

    assert sha256(source).hexdigest() == source_manifest.content_hash
    assert source_manifest.library_version == "6.1.0"
    assert source_manifest.source_commit == "56384e5afed6d1ad122e19b1bf3a7885fc38e5e5"
    assert source_manifest.license_name == "Apache-2.0"


def test_source_fetcher_rejects_modified_content(
    source_manifest: SourceManifest,
    tmp_path: Path,
) -> None:
    modified_source = tmp_path / "modified.html"
    modified_source.write_text("<html>modified</html>", encoding="utf-8")

    with pytest.raises(SourceIntegrityError, match="source hash mismatch"):
        LocalFileSourceFetcher(modified_source).fetch(source_manifest)


def test_sphinx_parser_preserves_api_structure(
    source_manifest: SourceManifest,
    source_path: Path,
) -> None:
    source = LocalFileSourceFetcher(source_path).fetch(source_manifest)
    parsed = SphinxApiParser().parse(source, source_manifest)
    sections = {section.name: section for section in parsed.sections}

    assert parsed.api_symbol == "pymc.sample"
    assert parsed.signature.startswith("pymc.sample(draws=1000,*")
    assert "[source]" not in parsed.signature
    assert list(sections) == ["Overview", "Parameters", "Returns", "Notes", "Examples"]
    assert "Draw samples from the posterior" in sections["Overview"].content
    assert "random_seed" in sections["Parameters"].content
    assert "arviz.InferenceData" in sections["Returns"].content
    assert "pm.NUTS" in sections["Notes"].content
    assert "pm.sample()" in sections["Examples"].content
    assert sections["Notes"].contains_code
    assert sections["Examples"].contains_code
    assert parsed.document.parser_version == "sphinx-api-v1"
    assert parsed.document.library_version == "6.1.0"


def test_sphinx_parser_rejects_unexpected_symbol(
    source_manifest: SourceManifest,
    source_path: Path,
) -> None:
    source = LocalFileSourceFetcher(source_path).fetch(source_manifest)
    wrong_manifest = source_manifest.model_copy(
        update={"expected_api_symbol": "pymc.sample_prior_predictive"}
    )

    with pytest.raises(DocumentParseError, match="expected API symbol"):
        SphinxApiParser().parse(source, wrong_manifest)


def test_api_chunker_is_deterministic_and_preserves_sections(
    source_manifest: SourceManifest,
    source_path: Path,
) -> None:
    source = LocalFileSourceFetcher(source_path).fetch(source_manifest)
    parsed = SphinxApiParser().parse(source, source_manifest)
    chunker = ApiReferenceChunker()

    first = chunker.chunk(parsed)
    second = chunker.chunk(parsed)

    assert len(first) == 5
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert [chunk.section for chunk in first] == [
        "Overview",
        "Parameters",
        "Returns",
        "Notes",
        "Examples",
    ]
    assert all(chunk.api_symbols == ("pymc.sample",) for chunk in first)
    assert all(chunk.library_version == "6.1.0" for chunk in first)
    assert all(chunk.chunker_version == "api-reference-v1" for chunk in first)
    assert {chunk.section for chunk in first if chunk.contains_code} == {
        "Notes",
        "Examples",
    }
