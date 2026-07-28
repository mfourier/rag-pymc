"""Retrieval-to-answer orchestration for the expert-assistant boundary."""

from dataclasses import dataclass

from rag_pymc.abstention.protocols import AbstentionPolicy
from rag_pymc.context.protocols import ContextBuilder
from rag_pymc.domain import (
    ConstructedContext,
    EvidenceAssessment,
    GeneratorInput,
    GeneratorOutput,
    GroundedAnswer,
    SearchQuery,
)
from rag_pymc.generation.protocols import AnswerGenerator
from rag_pymc.retrieval.protocols import Retriever


@dataclass(frozen=True, slots=True)
class ExpertAssistantResult:
    """Exact evidence, policy decision, and optional validated generation result."""

    context: ConstructedContext
    assessment: EvidenceAssessment
    answer: GroundedAnswer
    generator_output: GeneratorOutput | None

    def __post_init__(self) -> None:
        """Keep abstention and generation outcomes bound to the same context."""
        if self.assessment.context_chunk_ids != self.context.included_chunk_ids:
            raise ValueError("assistant assessment context IDs do not match its context")
        if self.assessment.omitted_chunk_ids != self.context.omitted_chunk_ids:
            raise ValueError("assistant assessment omitted IDs do not match its context")
        if self.assessment.should_abstain:
            if not self.answer.is_abstaining or self.generator_output is not None:
                raise ValueError("assistant policy abstention must bypass generation")
        elif self.generator_output is None or self.generator_output.answer != self.answer:
            raise ValueError(
                "assistant authorized answers require their validated generator output"
            )


@dataclass(frozen=True, slots=True)
class ExpertAssistantService:
    """Retrieve, construct context, assess evidence, and conditionally generate."""

    retriever: Retriever
    context_builder: ContextBuilder
    abstention_policy: AbstentionPolicy
    generator: AnswerGenerator

    def answer(self, query: SearchQuery, *, token_budget: int) -> ExpertAssistantResult:
        """Return a clean abstention or one output validated against authorized evidence."""
        retrieved = self.retriever.retrieve(query)
        context = self.context_builder.build(query, retrieved, token_budget=token_budget)
        assessment = self.abstention_policy.assess(context)
        if assessment.should_abstain:
            return ExpertAssistantResult(
                context=context,
                assessment=assessment,
                answer=GroundedAnswer(is_abstaining=True),
                generator_output=None,
            )

        generator_input = GeneratorInput(
            query=query,
            context=context,
            assessment=assessment,
        )
        answer = self.generator.generate(generator_input)
        output = GeneratorOutput(generator_input=generator_input, answer=answer)
        return ExpertAssistantResult(
            context=context,
            assessment=assessment,
            answer=answer,
            generator_output=output,
        )
