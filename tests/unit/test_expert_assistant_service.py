from datetime import UTC, datetime
from hashlib import sha256

from pydantic import AnyUrl

from rag_pymc.abstention import ConservativeAbstentionPolicy
from rag_pymc.abstention.protocols import AbstentionPolicy
from rag_pymc.application.expert_assistant import ExpertAssistantService
from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import (
    Chunk,
    ConstructedContext,
    EvidenceAssessment,
    EvidenceSufficiency,
    GeneratorInput,
    GroundedAnswer,
    RetrievedChunk,
    SearchQuery,
    SourceType,
)
from rag_pymc.retrieval import TechnicalTokenizer


class StaticRetriever:
    def __init__(self, result: RetrievedChunk) -> None:
        self.result = result
        self.calls = 0

    def retrieve(self, query: SearchQuery) -> list[RetrievedChunk]:
        self.calls += 1
        return [self.result]


class SufficientPolicy:
    name = "sufficient-test-policy-v1"

    def assess(self, context: ConstructedContext) -> EvidenceAssessment:
        return EvidenceAssessment(
            policy_version=self.name,
            sufficiency=EvidenceSufficiency.SUFFICIENT,
            should_abstain=False,
            reason_codes=("synthetic_sufficiency",),
            context_chunk_ids=context.included_chunk_ids,
            omitted_chunk_ids=context.omitted_chunk_ids,
        )


class RecordingGenerator:
    name = "recording-generator-v1"

    def __init__(self) -> None:
        self.inputs: list[GeneratorInput] = []

    def generate(self, generator_input: GeneratorInput) -> GroundedAnswer:
        self.inputs.append(generator_input)
        return GroundedAnswer(is_abstaining=True)


def make_result() -> RetrievedChunk:
    content = "pymc.sample draws samples from the posterior."
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id="chunk_sample",
            document_id="document_sample",
            library="pymc",
            library_version="6.1.0",
            source_type=SourceType.API_REFERENCE,
            source_url=AnyUrl("https://docs.example.test/pymc.sample.html"),
            title="pymc.sample",
            section="Overview",
            content=content,
            content_hash=sha256(content.encode()).hexdigest(),
            api_symbols=("pymc.sample",),
            created_at=datetime(2026, 7, 28, tzinfo=UTC),
        ),
        score=1.0,
        rank=1,
        retriever="bm25-v1",
    )


def make_service(
    policy: AbstentionPolicy,
    generator: RecordingGenerator,
) -> ExpertAssistantService:
    return ExpertAssistantService(
        retriever=StaticRetriever(make_result()),
        context_builder=RankedContextBuilder(TechnicalTokenizer()),
        abstention_policy=policy,
        generator=generator,
    )


def test_conservative_policy_returns_clean_abstention_without_calling_generator() -> None:
    generator = RecordingGenerator()
    service = make_service(ConservativeAbstentionPolicy(), generator)
    query = SearchQuery(text="What does pymc.sample do?", library="pymc")

    result = service.answer(query, token_budget=10_000)

    assert result.assessment.should_abstain is True
    assert result.answer == GroundedAnswer(is_abstaining=True)
    assert result.generator_output is None
    assert generator.inputs == []


def test_sufficient_policy_calls_generator_once_with_exact_bound_context() -> None:
    generator = RecordingGenerator()
    service = make_service(SufficientPolicy(), generator)
    query = SearchQuery(text="What does pymc.sample do?", library="pymc")

    result = service.answer(query, token_budget=10_000)

    assert len(generator.inputs) == 1
    assert generator.inputs[0].context == result.context
    assert generator.inputs[0].assessment == result.assessment
    assert result.generator_output is not None
    assert result.generator_output.generator_input == generator.inputs[0]
