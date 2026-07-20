"""Structure-aware chunking for API reference documents."""

from hashlib import sha256

from rag_pymc.domain import Chunk
from rag_pymc.parsing import ParsedApiDocument


class ApiReferenceChunker:
    """Create one retrieval unit for each semantic API section."""

    version = "api-reference-v1"

    def chunk(self, parsed: ParsedApiDocument) -> list[Chunk]:
        """Create deterministic chunks without splitting semantic sections."""
        chunks: list[Chunk] = []
        document = parsed.document

        for section in parsed.sections:
            content = (
                f"API symbol: {parsed.api_symbol}\n"
                f"Signature: {parsed.signature}\n"
                f"Section: {section.name}\n\n"
                f"{section.content}"
            )
            content_hash = sha256(content.encode("utf-8")).hexdigest()
            identity = f"{document.document_id}\0{section.name}\0{content_hash}".encode()
            chunk_id = f"chunk_{sha256(identity).hexdigest()[:20]}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    library=document.library,
                    library_version=document.library_version,
                    source_type=document.source_type,
                    source_url=document.source_url,
                    title=document.title,
                    section=section.name,
                    content=content,
                    content_hash=content_hash,
                    api_symbols=(parsed.api_symbol,),
                    contains_code=section.contains_code,
                    language=document.language,
                    created_at=document.fetched_at,
                    chunker_version=self.version,
                )
            )

        return chunks
