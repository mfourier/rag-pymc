"""Offline integration tests for the authorized MCP evidence vertical slice."""

import json
import shutil
import sys
from pathlib import Path

import anyio
import pytest
from mcp.client import ClientSession
from mcp.client._memory import InMemoryTransport
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

from rag_pymc.application.evidence import (
    GetEvidenceChunkResult,
    InspectEvidenceContextResult,
    SearchEvidenceResult,
)
from rag_pymc.application.evidence_runtime import (
    AuthorizedCorpusLoadError,
    build_default_evidence_service,
)
from rag_pymc.chunking import ApiReferenceChunker
from rag_pymc.domain import SourceManifest
from rag_pymc.ingestion import IngestionService, LocalFileSourceFetcher
from rag_pymc.mcp.registry import (
    EvidenceToolInvocationError,
    EvidenceToolRegistry,
)
from rag_pymc.mcp.stdio import build_mcp_server
from rag_pymc.parsing import SphinxApiParser
from rag_pymc.persistence import JsonDocumentRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FREEZE_PATH = PROJECT_ROOT / "reports/evaluation/pymc-6.2.0-api-v1-freeze.json"
SOURCE_NAMES = (
    "pymc.Data",
    "pymc.model.core.set_data",
    "pymc.sample",
    "pymc.sample_posterior_predictive",
)


@pytest.fixture
def evidence_registry(tmp_path: Path) -> EvidenceToolRegistry:
    corpus_dir = tmp_path / "corpus"
    _build_authorized_corpus(corpus_dir)
    return EvidenceToolRegistry(
        build_default_evidence_service(corpus_dir=corpus_dir, freeze_path=FREEZE_PATH)
    )


def _build_authorized_corpus(corpus_dir: Path) -> None:
    repository = JsonDocumentRepository(corpus_dir)
    for source_name in SOURCE_NAMES:
        manifest_path = PROJECT_ROOT / f"datasets/raw/manifests/pymc/6.2.0/{source_name}.json"
        source_path = PROJECT_ROOT / f"datasets/fixtures/pymc/6.2.0/{source_name}.html"
        manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        IngestionService(
            fetcher=LocalFileSourceFetcher(source_path),
            parser=SphinxApiParser(),
            chunker=ApiReferenceChunker(),
            repository=repository,
        ).run(manifest)


def test_fake_in_process_client_lists_and_calls_all_read_only_tools(
    evidence_registry: EvidenceToolRegistry,
) -> None:
    definitions = evidence_registry.list_tools()

    assert tuple(item.name for item in definitions) == (
        "search_pymc_evidence",
        "inspect_pymc_context",
        "get_pymc_chunk",
    )
    assert all(item.read_only for item in definitions)
    assert all(item.input_schema["additionalProperties"] is False for item in definitions)

    search = evidence_registry.call_tool(
        "search_pymc_evidence",
        {"query": "How do I update model data?", "version": "6.2.0", "top_k": 3},
    )
    repeated = evidence_registry.call_tool(
        "search_pymc_evidence",
        {"query": "How do I update model data?", "version": "6.2.0", "top_k": 3},
    )
    assert search.model_dump_json() == repeated.model_dump_json()
    assert isinstance(search.result, SearchEvidenceResult)
    assert search.result.chunk_ids

    context = evidence_registry.call_tool(
        "inspect_pymc_context",
        {
            "query": "How do I update model data?",
            "version": "6.2.0",
            "token_budget": 2048,
        },
    )
    assert isinstance(context.result, InspectEvidenceContextResult)
    assert context.result.authorization.should_abstain is True
    assert context.result.authorization.generation_permitted is False
    assert context.result.assessment.policy_version == "conservative-no-threshold-v1"

    chunk = evidence_registry.call_tool(
        "get_pymc_chunk",
        {"chunk_id": search.result.chunk_ids[0], "version": "6.2.0"},
    )
    assert isinstance(chunk.result, GetEvidenceChunkResult)
    assert chunk.result.chunk.chunk_id == search.result.chunk_ids[0]
    assert chunk.result.chunk.text
    assert str(chunk.result.chunk.provenance.source_url).startswith("https://www.pymc.io/")


@pytest.mark.anyio
async def test_official_sdk_in_process_client_lists_calls_and_validates_output_schema(
    evidence_registry: EvidenceToolRegistry,
) -> None:
    server = build_mcp_server(evidence_registry)

    async with (
        InMemoryTransport(server, raise_exceptions=True) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        initialized = await session.initialize()
        listed = await session.list_tools()
        result = await session.call_tool(
            "search_pymc_evidence",
            {"query": "posterior predictive", "version": "6.2.0", "top_k": 2},
        )
        invalid = await session.call_tool(
            "search_pymc_evidence",
            {
                "query": "posterior predictive",
                "version": "6.2.0",
                "top_k": 2,
                "path": "/private/corpus.json",
            },
        )

    assert initialized.server_info.name == "rag-pymc"
    assert initialized.server_info.version == "rag-pymc-mcp-evidence-v1"
    assert initialized.capabilities.resources is None
    assert initialized.capabilities.prompts is None
    assert [tool.name for tool in listed.tools] == [
        "search_pymc_evidence",
        "inspect_pymc_context",
        "get_pymc_chunk",
    ]
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in listed.tools)
    assert all(
        tool.annotations and tool.annotations.open_world_hint is False for tool in listed.tools
    )
    for tool in listed.tools:
        assert tool.output_schema is not None
        assert tool.output_schema["properties"]["tool_name"]["const"] == tool.name
    assert result.is_error is False
    assert result.structured_content["schema_version"] == "rag-pymc-mcp-tool-result-v1"
    assert result.structured_content["result"]["authorization"]["generation_permitted"] is False
    assert invalid.is_error is True
    assert invalid.structured_content["code"] == "invalid_arguments"
    assert isinstance(invalid.content[0], TextContent)
    assert "/private/corpus.json" not in invalid.content[0].text


@pytest.mark.anyio
async def test_official_sdk_stdio_transport_is_offline_and_keeps_stdout_protocol_clean(
    tmp_path: Path,
) -> None:
    corpus_dir = tmp_path / "datasets/processed/pymc-6.2.0-api-v1"
    freeze_path = tmp_path / "reports/evaluation/pymc-6.2.0-api-v1-freeze.json"
    _build_authorized_corpus(corpus_dir)
    freeze_path.parent.mkdir(parents=True)
    shutil.copyfile(FREEZE_PATH, freeze_path)
    error_log_path = tmp_path / "mcp-stderr.log"
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "rag_pymc.cli", "serve-mcp"],
        cwd=tmp_path,
    )

    with (
        error_log_path.open("w", encoding="utf-8") as error_log,
        anyio.fail_after(15),
    ):
        async with (
            stdio_client(parameters, errlog=error_log) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()
            listed = await session.list_tools()
            result = await session.call_tool(
                "inspect_pymc_context",
                {
                    "query": "How do I draw posterior samples?",
                    "version": "6.2.0",
                    "token_budget": 512,
                },
            )

    assert [tool.name for tool in listed.tools] == [
        "search_pymc_evidence",
        "inspect_pymc_context",
        "get_pymc_chunk",
    ]
    assert result.is_error is False
    assert result.structured_content["result"]["authorization"]["should_abstain"] is True
    assert error_log_path.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    ("tool_name", "arguments", "error_code"),
    [
        (
            "search_pymc_evidence",
            {"query": "query", "version": "6.1.0", "top_k": 3},
            "invalid_arguments",
        ),
        (
            "search_pymc_evidence",
            {"query": "query", "version": "6.2.0", "top_k": 11},
            "invalid_arguments",
        ),
        (
            "inspect_pymc_context",
            {"query": "query", "version": "6.2.0", "token_budget": 8193},
            "invalid_arguments",
        ),
        (
            "get_pymc_chunk",
            {"chunk_id": "chunk_ffffffffffffffffffff", "version": "6.2.0"},
            "chunk_not_found",
        ),
        (
            "get_pymc_chunk",
            {"chunk_id": "/etc/passwd", "version": "6.2.0", "corpus_dir": "/secret"},
            "invalid_arguments",
        ),
        ("read_file", {"path": "/etc/passwd"}, "unknown_tool"),
    ],
)
def test_tool_errors_fail_closed_without_leaking_inputs_or_paths(
    evidence_registry: EvidenceToolRegistry,
    tool_name: str,
    arguments: dict[str, object],
    error_code: str,
) -> None:
    with pytest.raises(EvidenceToolInvocationError) as raised:
        evidence_registry.call_tool(tool_name, arguments)

    payload = raised.value.payload
    serialized = payload.model_dump_json()
    assert payload.code == error_code
    assert "/etc/passwd" not in serialized
    assert "/secret" not in serialized
    assert "rag-pymc-mcp-tool-error-v1" in serialized


def test_absent_empty_or_tampered_corpus_fails_closed_without_path_disclosure(
    tmp_path: Path,
) -> None:
    absent = tmp_path / "private" / "missing-corpus"
    with pytest.raises(AuthorizedCorpusLoadError) as missing:
        build_default_evidence_service(corpus_dir=absent, freeze_path=FREEZE_PATH)
    assert str(absent) not in str(missing.value)

    empty = tmp_path / "empty-corpus"
    empty.mkdir()
    (empty / "corpus.json").write_text(
        '{"schema_version":"1","documents":[],"chunks":[]}\n',
        encoding="utf-8",
    )
    with pytest.raises(AuthorizedCorpusLoadError, match="unavailable or empty") as empty_error:
        build_default_evidence_service(corpus_dir=empty, freeze_path=FREEZE_PATH)
    assert str(empty) not in str(empty_error.value)

    tampered_freeze = tmp_path / "freeze.json"
    payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    payload["corpus_sha256"] = "0" * 64
    tampered_freeze.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(AuthorizedCorpusLoadError) as tampered:
        build_default_evidence_service(
            corpus_dir=absent,
            freeze_path=tampered_freeze,
        )
    assert str(tampered_freeze) not in str(tampered.value)
