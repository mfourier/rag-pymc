from typing import Never, cast

import pytest

import rag_pymc.mcp.stdio as mcp_stdio
from rag_pymc.mcp.registry import EvidenceToolRegistry


def test_stdio_startup_sanitizes_unexpected_transport_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = cast(EvidenceToolRegistry, object())

    def fail_transport(_registry: EvidenceToolRegistry) -> Never:
        raise RuntimeError("unexpected failure at /private/transport")

    monkeypatch.setattr(mcp_stdio, "build_default_tool_registry", lambda: registry)
    monkeypatch.setattr(mcp_stdio, "build_mcp_server", fail_transport)

    with pytest.raises(mcp_stdio.McpServerStartupError) as raised:
        mcp_stdio.serve_stdio()

    assert str(raised.value) == "MCP STDIO server failed closed"
    assert "/private/transport" not in str(raised.value)
