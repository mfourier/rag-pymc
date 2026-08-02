"""SDK-independent registry for deterministic MCP evidence tools."""

from collections.abc import Mapping
from typing import Final, Literal

from pydantic import Field, ValidationError

from rag_pymc.application.evidence import (
    EvidenceInspectionService,
    EvidenceModel,
    GetEvidenceChunkRequest,
    GetEvidenceChunkResult,
    InspectEvidenceContextRequest,
    InspectEvidenceContextResult,
    SearchEvidenceRequest,
    SearchEvidenceResult,
    UnknownEvidenceChunkError,
)
from rag_pymc.application.evidence_runtime import (
    AuthorizedCorpusLoadError,
    build_default_evidence_service,
)

MCP_EVIDENCE_SERVER_VERSION: Final = "rag-pymc-mcp-evidence-v1"
SEARCH_TOOL_NAME: Final[Literal["search_pymc_evidence"]] = "search_pymc_evidence"
INSPECT_TOOL_NAME: Final[Literal["inspect_pymc_context"]] = "inspect_pymc_context"
GET_CHUNK_TOOL_NAME: Final[Literal["get_pymc_chunk"]] = "get_pymc_chunk"


class EvidenceToolDefinition(EvidenceModel):
    """Portable tool metadata consumed by the SDK adapter and offline tests."""

    name: Literal[
        "search_pymc_evidence",
        "inspect_pymc_context",
        "get_pymc_chunk",
    ]
    tool_version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    read_only: Literal[True] = True
    input_schema: dict[str, object]
    output_schema: dict[str, object]


class _EvidenceToolResultEnvelopeBase(EvidenceModel):
    """Shared identities present in every successful tool envelope."""

    schema_version: Literal["rag-pymc-mcp-tool-result-v1"] = "rag-pymc-mcp-tool-result-v1"
    server_version: Literal["rag-pymc-mcp-evidence-v1"] = "rag-pymc-mcp-evidence-v1"


class SearchEvidenceToolResultEnvelope(_EvidenceToolResultEnvelopeBase):
    """Output schema bound exactly to the evidence-search tool."""

    tool_name: Literal["search_pymc_evidence"] = "search_pymc_evidence"
    tool_version: Literal["search-pymc-evidence-v1"] = "search-pymc-evidence-v1"
    result: SearchEvidenceResult


class InspectContextToolResultEnvelope(_EvidenceToolResultEnvelopeBase):
    """Output schema bound exactly to the context-inspection tool."""

    tool_name: Literal["inspect_pymc_context"] = "inspect_pymc_context"
    tool_version: Literal["inspect-pymc-context-v1"] = "inspect-pymc-context-v1"
    result: InspectEvidenceContextResult


class GetChunkToolResultEnvelope(_EvidenceToolResultEnvelopeBase):
    """Output schema bound exactly to authorized chunk lookup."""

    tool_name: Literal["get_pymc_chunk"] = "get_pymc_chunk"
    tool_version: Literal["get-pymc-chunk-v1"] = "get-pymc-chunk-v1"
    result: GetEvidenceChunkResult


EvidenceToolResultEnvelope = (
    SearchEvidenceToolResultEnvelope | InspectContextToolResultEnvelope | GetChunkToolResultEnvelope
)


class EvidenceToolErrorPayload(EvidenceModel):
    """Sanitized deterministic error safe for an MCP client."""

    schema_version: Literal["rag-pymc-mcp-tool-error-v1"] = "rag-pymc-mcp-tool-error-v1"
    server_version: Literal["rag-pymc-mcp-evidence-v1"] = "rag-pymc-mcp-evidence-v1"
    code: Literal[
        "unknown_tool",
        "invalid_arguments",
        "chunk_not_found",
        "corpus_unavailable",
        "internal_error",
    ]
    message: str = Field(min_length=1, max_length=240)


class EvidenceToolInvocationError(ValueError):
    """Carry a structured error without exposing exception causes or local paths."""

    def __init__(self, payload: EvidenceToolErrorPayload) -> None:
        """Store one client-safe structured error payload."""
        super().__init__(payload.message)
        self.payload = payload


class EvidenceToolRegistry:
    """List and invoke the fixed read-only evidence surface in process."""

    def __init__(self, service: EvidenceInspectionService) -> None:
        """Bind the fixed tool surface to one project-owned evidence service."""
        self._service = service
        self._definitions = _tool_definitions()

    def list_tools(self) -> tuple[EvidenceToolDefinition, ...]:
        """Return a stable ordered tool list without dynamic discovery."""
        return self._definitions

    def call_tool(
        self,
        name: str,
        arguments: Mapping[str, object],
    ) -> EvidenceToolResultEnvelope:
        """Validate strict arguments and invoke exactly one application-service method."""
        definition = next((item for item in self._definitions if item.name == name), None)
        if definition is None:
            raise EvidenceToolInvocationError(
                EvidenceToolErrorPayload(
                    code="unknown_tool",
                    message="requested tool is not part of the read-only PyMC evidence server",
                )
            )
        try:
            if name == SEARCH_TOOL_NAME:
                search_result = self._service.search(
                    SearchEvidenceRequest.model_validate(arguments)
                )
            elif name == INSPECT_TOOL_NAME:
                context_result = self._service.inspect_context(
                    InspectEvidenceContextRequest.model_validate(arguments)
                )
            else:
                chunk_result = self._service.get_chunk(
                    GetEvidenceChunkRequest.model_validate(arguments)
                )
        except ValidationError as error:
            raise EvidenceToolInvocationError(_validation_error_payload(error)) from None
        except UnknownEvidenceChunkError:
            raise EvidenceToolInvocationError(
                EvidenceToolErrorPayload(
                    code="chunk_not_found",
                    message="chunk ID is not present in the authorized PyMC corpus",
                )
            ) from None
        except AuthorizedCorpusLoadError:
            raise EvidenceToolInvocationError(
                EvidenceToolErrorPayload(
                    code="corpus_unavailable",
                    message="authorized PyMC corpus is unavailable or invalid",
                )
            ) from None
        except Exception:
            raise EvidenceToolInvocationError(
                EvidenceToolErrorPayload(
                    code="internal_error",
                    message="read-only evidence tool failed closed",
                )
            ) from None
        if name == SEARCH_TOOL_NAME:
            return SearchEvidenceToolResultEnvelope(result=search_result)
        if name == INSPECT_TOOL_NAME:
            return InspectContextToolResultEnvelope(result=context_result)
        return GetChunkToolResultEnvelope(result=chunk_result)


def build_default_tool_registry() -> EvidenceToolRegistry:
    """Compose the fixed repository-local evidence server."""
    return EvidenceToolRegistry(build_default_evidence_service())


def _tool_definitions() -> tuple[EvidenceToolDefinition, ...]:
    return (
        EvidenceToolDefinition(
            name=SEARCH_TOOL_NAME,
            tool_version="search-pymc-evidence-v1",
            description=(
                "Search only the authorized official PyMC 6.2.0 corpus with deterministic BM25. "
                "Returns evidence and an abstention state, never an answer."
            ),
            input_schema=SearchEvidenceRequest.model_json_schema(),
            output_schema=SearchEvidenceToolResultEnvelope.model_json_schema(),
        ),
        EvidenceToolDefinition(
            name=INSPECT_TOOL_NAME,
            tool_version="inspect-pymc-context-v1",
            description=(
                "Construct deterministic bounded context from the authorized PyMC 6.2.0 corpus "
                "and expose the conservative sufficiency assessment."
            ),
            input_schema=InspectEvidenceContextRequest.model_json_schema(),
            output_schema=InspectContextToolResultEnvelope.model_json_schema(),
        ),
        EvidenceToolDefinition(
            name=GET_CHUNK_TOOL_NAME,
            tool_version="get-pymc-chunk-v1",
            description=(
                "Resolve one opaque chunk ID that already belongs to the authorized PyMC 6.2.0 "
                "corpus. No filesystem path or URL input is accepted."
            ),
            input_schema=GetEvidenceChunkRequest.model_json_schema(),
            output_schema=GetChunkToolResultEnvelope.model_json_schema(),
        ),
    )


def _validation_error_payload(error: ValidationError) -> EvidenceToolErrorPayload:
    fields = tuple(
        sorted(
            {
                str(item["loc"][0]) if item["loc"] else "arguments"
                for item in error.errors(include_input=False, include_url=False)
            }
        )
    )
    rendered_fields = ", ".join(fields)
    if "version" in fields:
        message = "version must be explicit and supported; supported versions: 6.2.0"
    else:
        message = f"invalid value for field(s): {rendered_fields}"
    return EvidenceToolErrorPayload(code="invalid_arguments", message=message)
