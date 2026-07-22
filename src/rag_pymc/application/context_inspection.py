"""Application use case for retrieving and constructing inspectable context."""

from dataclasses import dataclass

from rag_pymc.context.protocols import ContextBuilder
from rag_pymc.domain import ConstructedContext, SearchQuery
from rag_pymc.retrieval.protocols import Retriever


@dataclass(frozen=True, slots=True)
class ContextInspectionService:
    """Coordinate one retrieval call and one deterministic context build."""

    retriever: Retriever
    context_builder: ContextBuilder

    def inspect(self, query: SearchQuery, *, token_budget: int) -> ConstructedContext:
        """Retrieve ranked evidence and return the exact constructed context."""
        retrieved = self.retriever.retrieve(query)
        return self.context_builder.build(query, retrieved, token_budget=token_budget)
