"""Section- and cell-aware chunking for normalized notebooks."""

from collections import defaultdict
from hashlib import sha256

from rag_pymc.domain import Chunk
from rag_pymc.parsing import ParsedNotebookCell, ParsedNotebookDocument


class NotebookChunker:
    """Group adjacent notebook inputs without splitting individual cells."""

    version = "notebook-cells-v1"

    def __init__(self, *, max_cell_chars: int = 2_400) -> None:
        """Set the target payload size while preserving complete cells."""
        if max_cell_chars < 1_000:
            raise ValueError("max_cell_chars must be at least 1000")
        self.max_cell_chars = max_cell_chars

    def chunk(self, parsed: ParsedNotebookDocument) -> list[Chunk]:
        """Create deterministic chunks from adjacent cells in one section."""
        groups = self._group_cells(parsed.cells)
        section_counts: defaultdict[str, int] = defaultdict(int)
        chunks: list[Chunk] = []
        for cells in groups:
            section = cells[0].section
            section_counts[section] += 1
            part = section_counts[section]
            same_section_total = sum(group[0].section == section for group in groups)
            chunk_section = section if same_section_total == 1 else f"{section} [part {part}]"
            chunks.append(self._make_chunk(parsed, cells, chunk_section))
        return chunks

    def _group_cells(
        self,
        cells: tuple[ParsedNotebookCell, ...],
    ) -> tuple[tuple[ParsedNotebookCell, ...], ...]:
        groups: list[tuple[ParsedNotebookCell, ...]] = []
        pending: list[ParsedNotebookCell] = []
        pending_chars = 0
        for cell in cells:
            same_section = not pending or pending[-1].section == cell.section
            separator_chars = 2 if pending else 0
            proposed_chars = pending_chars + separator_chars + len(cell.content)
            if pending and (not same_section or proposed_chars > self.max_cell_chars):
                groups.append(tuple(pending))
                pending = []
                pending_chars = 0
            pending.append(cell)
            pending_chars += (2 if pending_chars else 0) + len(cell.content)
        if pending:
            groups.append(tuple(pending))
        return tuple(groups)

    def _make_chunk(
        self,
        parsed: ParsedNotebookDocument,
        cells: tuple[ParsedNotebookCell, ...],
        section: str,
    ) -> Chunk:
        rendered_cells = "\n\n".join(self._render_cell(cell) for cell in cells)
        cell_numbers = ", ".join(str(cell.cell_number) for cell in cells)
        content = "\n".join(
            (
                f"Notebook: {parsed.title}",
                f"Source path: {parsed.source_path}",
                f"Section: {section}",
                f"Cells: {cell_numbers}",
                "",
                rendered_cells,
            )
        )
        content_hash = sha256(content.encode("utf-8")).hexdigest()
        identity = f"{parsed.document.document_id}\0{section}\0{content_hash}".encode()
        chunk_id = f"chunk_{sha256(identity).hexdigest()[:20]}"
        api_symbols = tuple(sorted({symbol for cell in cells for symbol in cell.api_symbols}))
        document = parsed.document
        return Chunk(
            chunk_id=chunk_id,
            document_id=document.document_id,
            library=document.library,
            library_version=document.library_version,
            source_type=document.source_type,
            source_url=document.source_url,
            title=document.title,
            section=section,
            content=content,
            content_hash=content_hash,
            api_symbols=api_symbols,
            contains_code=any(cell.cell_type == "code" for cell in cells),
            language=document.language,
            created_at=document.fetched_at,
            chunker_version=self.version,
        )

    @staticmethod
    def _render_cell(cell: ParsedNotebookCell) -> str:
        heading = f"Cell {cell.cell_number} [{cell.cell_type}]"
        if cell.cell_type == "code":
            return f"{heading}\n```python\n{cell.content}\n```"
        return f"{heading}\n{cell.content}"
