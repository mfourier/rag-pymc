"""Structure-aware chunking for Python repository implementations."""

from hashlib import sha256

from rag_pymc.domain import Chunk
from rag_pymc.parsing import ParsedCodeBlock, ParsedRepositoryDocument


class RepositoryCodeChunker:
    """Create definition and bounded implementation chunks at AST boundaries."""

    version = "repository-code-ast-v1"

    def __init__(self, *, max_code_chars: int = 2_400) -> None:
        """Set the maximum code payload while keeping statements intact."""
        if max_code_chars < 1_000:
            raise ValueError("max_code_chars must be at least 1000")
        self.max_code_chars = max_code_chars

    def chunk(self, parsed: ParsedRepositoryDocument) -> list[Chunk]:
        """Create deterministic chunks for one parsed repository symbol."""
        definition = "\n".join(
            part
            for part in (
                f"Repository symbol: {parsed.api_symbol}",
                f"Source path: {parsed.source_path}",
                f"Symbol kind: {parsed.symbol_kind}",
                f"Lines: {parsed.start_line}-{parsed.end_line}",
                "",
                "Signature:",
                f"```python\n{parsed.signature}\n```",
                "",
                (
                    f"Docstring summary: {parsed.docstring_summary}"
                    if parsed.docstring_summary is not None
                    else None
                ),
            )
            if part is not None
        )
        chunks = [
            self._make_chunk(
                parsed,
                section="Definition",
                content=definition,
                contains_code=True,
            )
        ]
        for index, blocks in enumerate(self._group_blocks(parsed.blocks), start=1):
            start_line = blocks[0].start_line
            end_line = blocks[-1].end_line
            code = "\n\n".join(block.content for block in blocks)
            content = "\n".join(
                (
                    f"Repository symbol: {parsed.api_symbol}",
                    f"Source path: {parsed.source_path}",
                    f"Implementation lines: {start_line}-{end_line}",
                    "",
                    "```python",
                    code,
                    "```",
                )
            )
            chunks.append(
                self._make_chunk(
                    parsed,
                    section=f"Implementation {index}",
                    content=content,
                    contains_code=True,
                )
            )
        return chunks

    def _group_blocks(
        self,
        blocks: tuple[ParsedCodeBlock, ...],
    ) -> tuple[tuple[ParsedCodeBlock, ...], ...]:
        groups: list[tuple[ParsedCodeBlock, ...]] = []
        pending: list[ParsedCodeBlock] = []
        pending_chars = 0
        for block in blocks:
            separator_chars = 2 if pending else 0
            proposed_chars = pending_chars + separator_chars + len(block.content)
            if pending and proposed_chars > self.max_code_chars:
                groups.append(tuple(pending))
                pending = []
                pending_chars = 0
            pending.append(block)
            pending_chars += (2 if pending_chars else 0) + len(block.content)
        if pending:
            groups.append(tuple(pending))
        return tuple(groups)

    def _make_chunk(
        self,
        parsed: ParsedRepositoryDocument,
        *,
        section: str,
        content: str,
        contains_code: bool,
    ) -> Chunk:
        document = parsed.document
        content_hash = sha256(content.encode("utf-8")).hexdigest()
        identity = f"{document.document_id}\0{section}\0{content_hash}".encode()
        chunk_id = f"chunk_{sha256(identity).hexdigest()[:20]}"
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
            api_symbols=(parsed.api_symbol,),
            contains_code=contains_code,
            language=document.language,
            created_at=document.fetched_at,
            chunker_version=self.version,
        )
