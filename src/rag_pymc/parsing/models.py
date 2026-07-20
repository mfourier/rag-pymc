"""Intermediate structured values produced by source parsers."""

from pydantic import BaseModel, ConfigDict, Field

from rag_pymc.domain import Document


class ParsedSection(BaseModel):
    """A semantic section that must remain intact during chunking."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(min_length=1)
    content: str = Field(min_length=1)
    contains_code: bool = False


class ParsedApiDocument(BaseModel):
    """Normalized API documentation before retrieval chunk construction."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    document: Document
    api_symbol: str = Field(min_length=1)
    signature: str = Field(min_length=1)
    sections: tuple[ParsedSection, ...] = Field(min_length=1)
