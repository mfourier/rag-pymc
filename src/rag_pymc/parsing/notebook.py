"""Parser for controlled Jupyter notebook source files."""

import json
import re
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any

from rag_pymc.domain import Document, SourceManifest, SourceType
from rag_pymc.ingestion.errors import DocumentParseError
from rag_pymc.parsing.models import ParsedNotebookCell, ParsedNotebookDocument

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PYMC_SYMBOL_PATTERN = re.compile(r"\b(?:pm|pymc)\.([A-Za-z_]\w*)")


class NotebookParser:
    """Normalize Markdown and code inputs while excluding execution artifacts."""

    version = "jupyter-notebook-inputs-v1"

    def parse(self, source: bytes, manifest: SourceManifest) -> ParsedNotebookDocument:
        """Parse a verified notebook into ordered, section-aware input cells."""
        if manifest.source_type is not SourceType.NOTEBOOK:
            msg = f"NotebookParser does not support {manifest.source_type}"
            raise DocumentParseError(msg)
        if manifest.media_type != "application/x-ipynb+json":
            msg = f"expected application/x-ipynb+json, got {manifest.media_type}"
            raise DocumentParseError(msg)
        if manifest.source_path is None:
            raise DocumentParseError("notebook manifest is missing source_path")

        try:
            notebook: Any = json.loads(source)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise DocumentParseError("notebook source is not valid UTF-8 JSON") from error
        if not isinstance(notebook, dict) or not isinstance(notebook.get("cells"), list):
            raise DocumentParseError("notebook must contain a cells array")

        fallback_title = PurePosixPath(manifest.source_path).stem.replace("_", " ").title()
        title: str | None = None
        heading_stack: dict[int, str] = {}
        cells: list[ParsedNotebookCell] = []
        for cell_number, value in enumerate(notebook["cells"], start=1):
            if not isinstance(value, dict):
                raise DocumentParseError(f"notebook cell {cell_number} is not an object")
            cell_type = value.get("cell_type")
            if cell_type not in {"markdown", "code"}:
                continue
            content = self._cell_source(value, cell_number).strip()
            if not content:
                continue

            if cell_type == "markdown":
                cell_heading = self._update_headings(content, heading_stack)
                if cell_heading is not None and cell_heading[0] == 1 and title is None:
                    title = cell_heading[1]
            section = self._section(heading_stack, title or fallback_title)
            api_symbols = self._api_symbols(content) if cell_type == "code" else ()
            cells.append(
                ParsedNotebookCell(
                    cell_number=cell_number,
                    cell_type=cell_type,
                    section=section,
                    content=content,
                    api_symbols=api_symbols,
                )
            )

        if not cells:
            raise DocumentParseError("notebook contains no nonempty Markdown or code inputs")
        resolved_title = title or fallback_title
        normalized_content = self._document_content(
            resolved_title,
            manifest.source_path,
            cells,
        )
        content_hash = sha256(normalized_content.encode("utf-8")).hexdigest()
        document = Document(
            document_id=f"doc_{content_hash[:20]}",
            library=manifest.library,
            library_version=manifest.library_version,
            source_type=manifest.source_type,
            source_url=manifest.source_url,
            title=resolved_title,
            content=normalized_content,
            content_hash=content_hash,
            fetched_at=manifest.downloaded_at,
            source_commit=manifest.source_commit,
            license_name=manifest.license_name,
            license_url=manifest.license_url,
            parser_version=self.version,
        )
        return ParsedNotebookDocument(
            document=document,
            source_path=manifest.source_path,
            title=resolved_title,
            cells=tuple(cells),
        )

    @staticmethod
    def _cell_source(cell: dict[str, Any], cell_number: int) -> str:
        value = cell.get("source", "")
        if isinstance(value, str):
            return value
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return "".join(value)
        raise DocumentParseError(f"notebook cell {cell_number} has invalid source")

    @staticmethod
    def _update_headings(
        content: str,
        heading_stack: dict[int, str],
    ) -> tuple[int, str] | None:
        first_heading: tuple[int, str] | None = None
        for line in content.splitlines():
            match = HEADING_PATTERN.match(line.strip())
            if match is None:
                continue
            level = len(match.group(1))
            heading = match.group(2).strip()
            heading_stack[level] = heading
            for deeper_level in tuple(
                candidate for candidate in heading_stack if candidate > level
            ):
                del heading_stack[deeper_level]
            if first_heading is None:
                first_heading = (level, heading)
        return first_heading

    @staticmethod
    def _section(heading_stack: dict[int, str], fallback: str) -> str:
        headings = tuple(heading_stack[level] for level in sorted(heading_stack))
        return " > ".join(headings) if headings else fallback

    @staticmethod
    def _api_symbols(content: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    f"pymc.{match.group(1)}"
                    for match in PYMC_SYMBOL_PATTERN.finditer(content)
                    if not match.group(1).startswith("_")
                }
            )
        )

    @staticmethod
    def _document_content(
        title: str,
        source_path: str,
        cells: list[ParsedNotebookCell],
    ) -> str:
        parts = [f"# {title}", f"Source path: {source_path}"]
        for cell in cells:
            parts.extend(
                (
                    "",
                    (f"## Cell {cell.cell_number} [{cell.cell_type}] — {cell.section}"),
                    cell.content,
                )
            )
        return "\n".join(parts)
