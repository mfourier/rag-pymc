"""Project-owned abstention interfaces."""

from typing import Protocol

from rag_pymc.domain import ConstructedContext, EvidenceAssessment


class AbstentionPolicy(Protocol):
    """Assess whether constructed evidence permits a grounded answer."""

    name: str

    def assess(self, context: ConstructedContext) -> EvidenceAssessment:
        """Return a deterministic evidence assessment for one context."""
        ...
