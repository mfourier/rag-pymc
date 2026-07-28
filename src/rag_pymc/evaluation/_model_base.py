"""Shared strict primitives for evaluation artifact models."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


def _canonicalize_unique_strings(
    values: tuple[str, ...],
    *,
    label: str,
) -> tuple[str, ...]:
    if len(set(values)) != len(values):
        msg = f"{label} must be unique"
        raise ValueError(msg)
    return tuple(sorted(values))


class EvaluationModel(BaseModel):
    """Strict immutable base for evaluation artifacts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        revalidate_instances="always",
    )
