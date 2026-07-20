"""Shared metadata filtering for retrieval candidates."""

from rag_pymc.domain import Chunk, SearchQuery


def matches_filters(chunk: Chunk, query: SearchQuery) -> bool:
    """Return whether a chunk satisfies every explicit query filter."""
    if query.library is not None and chunk.library.casefold() != query.library.casefold():
        return False
    if query.library_version is not None and chunk.library_version != query.library_version:
        return False
    if query.source_types and chunk.source_type not in query.source_types:
        return False
    if query.api_symbols:
        chunk_symbols = {symbol.casefold() for symbol in chunk.api_symbols}
        if not all(symbol.casefold() in chunk_symbols for symbol in query.api_symbols):
            return False
    return True
