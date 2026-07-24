"""Intermediate structured values produced by source parsers."""

from typing import Literal

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


class ParsedCodeBlock(BaseModel):
    """One complete top-level statement from a repository symbol body."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    kind: Literal["statement"] = "statement"
    content: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)


class ParsedRepositoryDocument(BaseModel):
    """One normalized Python implementation selected from an upstream file."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    document: Document
    api_symbol: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    symbol_kind: Literal["function", "async_function", "class"]
    signature: str = Field(min_length=1)
    docstring_summary: str | None = None
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    blocks: tuple[ParsedCodeBlock, ...]


class ParsedNotebookCell(BaseModel):
    """One normalized Markdown or code input cell without execution output."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    cell_number: int = Field(ge=1)
    cell_type: Literal["markdown", "code"]
    section: str = Field(min_length=1)
    content: str = Field(min_length=1)
    api_symbols: tuple[str, ...] = ()


class ParsedNotebookDocument(BaseModel):
    """Normalized notebook narrative preserving cell and section identity."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    document: Document
    source_path: str = Field(min_length=1)
    title: str = Field(min_length=1)
    cells: tuple[ParsedNotebookCell, ...] = Field(min_length=1)
