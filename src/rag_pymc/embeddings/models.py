"""Validated embedding model provenance and runtime configuration."""

from pathlib import Path
from typing import Annotated

from pydantic import (
    AnyUrl,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
)

from rag_pymc.embeddings.errors import EmbeddingConfigurationError

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
GitRevision = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{40}$")]


class EmbeddingModelSpec(BaseModel):
    """Pinned identity and constraints for a remote embedding model."""

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
    dimension: int = Field(gt=0)
    max_sequence_length: int = Field(gt=0)
    trained_max_sequence_length: int = Field(gt=0)
    query_prefix: NonEmptyString | None = None
    normalize_embeddings: bool = True


def load_embedding_model_spec(path: Path) -> EmbeddingModelSpec:
    """Load a pinned embedding model specification from JSON."""
    try:
        return EmbeddingModelSpec.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError as error:
        msg = f"unable to read embedding model manifest: {path}"
        raise EmbeddingConfigurationError(msg) from error
    except ValidationError as error:
        msg = f"invalid embedding model manifest: {path}"
        raise EmbeddingConfigurationError(msg) from error
