"""Validated reranking model provenance and runtime configuration."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    AnyUrl,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
)

from rag_pymc.reranking.errors import RerankingConfigurationError

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
GitRevision = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{40}$")]


class RerankingModelSpec(BaseModel):
    """Pinned identity and constraints for a remote cross-encoder."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: NonEmptyString = "1"
    model_id: NonEmptyString
    revision: GitRevision
    source_url: AnyUrl
    source_last_modified_at: AwareDatetime
    downloaded_at: AwareDatetime
    license_name: NonEmptyString
    license_url: AnyUrl
    sentence_transformers_version: NonEmptyString
    max_sequence_length: int = Field(gt=0)
    backend: Literal["torch"] = "torch"
    score_function: Literal["identity_logit"] = "identity_logit"


def load_reranking_model_spec(path: Path) -> RerankingModelSpec:
    """Load a pinned reranking model specification from JSON."""
    try:
        return RerankingModelSpec.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError as error:
        msg = f"unable to read reranking model manifest: {path}"
        raise RerankingConfigurationError(msg) from error
    except ValidationError as error:
        msg = f"invalid reranking model manifest: {path}"
        raise RerankingConfigurationError(msg) from error
