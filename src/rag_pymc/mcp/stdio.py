"""Official-SDK STDIO adapter for the project-owned evidence tool registry."""

import json
import logging
import sys
from typing import Any

import anyio
import mcp.types as mcp_types
from mcp.server.context import ServerRequestContext
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from rag_pymc.application.evidence_runtime import AuthorizedCorpusLoadError
from rag_pymc.mcp.registry import (
    MCP_EVIDENCE_SERVER_VERSION,
    EvidenceToolInvocationError,
    EvidenceToolRegistry,
    build_default_tool_registry,
)


class McpServerStartupError(RuntimeError):
    """Raised when the fixed authorized evidence runtime cannot start safely."""


def build_mcp_server(registry: EvidenceToolRegistry) -> Server[dict[str, Any]]:
    """Adapt the fixed registry to official MCP types without moving validation into MCP."""

    async def list_tools(
        _context: ServerRequestContext[dict[str, Any]],
        _params: mcp_types.PaginatedRequestParams | None,
    ) -> mcp_types.ListToolsResult:
        tools = [
            mcp_types.Tool(
                name=definition.name,
                description=definition.description,
                input_schema=definition.input_schema,
                output_schema=definition.output_schema,
                annotations=mcp_types.ToolAnnotations(
                    read_only_hint=True,
                    destructive_hint=False,
                    idempotent_hint=True,
                    open_world_hint=False,
                ),
            )
            for definition in registry.list_tools()
        ]
        return mcp_types.ListToolsResult(tools=tools)

    async def call_tool(
        _context: ServerRequestContext[dict[str, Any]],
        params: mcp_types.CallToolRequestParams,
    ) -> mcp_types.CallToolResult:
        try:
            envelope = registry.call_tool(params.name, params.arguments or {})
        except EvidenceToolInvocationError as error:
            payload = error.payload.model_dump(mode="json")
            return mcp_types.CallToolResult(
                content=[mcp_types.TextContent(text=_canonical_json(payload))],
                structured_content=payload,
                is_error=True,
            )
        payload = envelope.model_dump(mode="json")
        return mcp_types.CallToolResult(
            content=[mcp_types.TextContent(text=_canonical_json(payload))],
            structured_content=payload,
        )

    return Server(
        "rag-pymc",
        version=MCP_EVIDENCE_SERVER_VERSION,
        title="rag-pymc read-only PyMC evidence",
        description=(
            "Deterministic read-only evidence access to the authorized official PyMC corpus; "
            "does not generate answers."
        ),
        instructions=(
            "Use these tools only to retrieve or inspect PyMC evidence. The returned "
            "authorization state currently forbids answer generation."
        ),
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


async def run_stdio_server(server: Server[dict[str, Any]]) -> None:
    """Run one already-composed server over STDIO using the official SDK."""
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(_stdio_scheduler_tick)
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
        task_group.cancel_scope.cancel()


def serve_stdio() -> None:
    """Load the authorized corpus and reserve stdout exclusively for MCP traffic."""
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, force=True)
    try:
        registry = build_default_tool_registry()
    except AuthorizedCorpusLoadError as error:
        raise McpServerStartupError(
            "authorized PyMC corpus is unavailable or invalid; MCP server did not start"
        ) from error
    try:
        anyio.run(run_stdio_server, build_mcp_server(registry))
    except Exception as error:
        raise McpServerStartupError("MCP STDIO server failed closed") from error


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


async def _stdio_scheduler_tick() -> None:
    """Wake blocking-file callbacks reliably on supported Conda Python 3.13 builds."""
    while True:
        await anyio.sleep(0.05)
