"""Provider-neutral interfaces for grounded answer generation."""

from typing import Protocol

from rag_pymc.domain import GeneratorInput, GroundedAnswer


class AnswerGenerator(Protocol):
    """Generate one structured answer from explicitly authorized evidence."""

    name: str

    def generate(self, generator_input: GeneratorInput) -> GroundedAnswer:
        """Return an answer that will be rebound and validated by the application."""
        ...
