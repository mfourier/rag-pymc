from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import AnyUrl, ValidationError

from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import (
    AtomicClaim,
    Chunk,
    Citation,
    ConstructedContext,
    ContextItem,
    EvidenceAssessment,
    EvidenceSufficiency,
    GeneratorInput,
    GeneratorOutput,
    GroundedAnswer,
    GroundedAnswerSection,
    RetrievedChunk,
    SearchQuery,
    SourceType,
)
from rag_pymc.retrieval import TechnicalTokenizer

NOW = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)


def make_result(
    chunk_id: str,
    *,
    rank: int,
    section: str | None,
    api_symbols: tuple[str, ...],
) -> RetrievedChunk:
    content = f"Complete evidence for {chunk_id}."
    chunk = Chunk(
        chunk_id=chunk_id,
        document_id=f"document_{chunk_id}",
        library="pymc",
        library_version="6.1.0",
        source_type=SourceType.API_REFERENCE,
        source_url=AnyUrl(f"https://docs.example.test/{chunk_id}.html"),
        title=f"Title for {chunk_id}",
        section=section,
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        api_symbols=api_symbols,
        created_at=NOW,
    )
    return RetrievedChunk(
        chunk=chunk,
        score=1.0 / rank,
        rank=rank,
        retriever="weighted-rrf-v1",
    )


def make_context() -> tuple[ConstructedContext, tuple[RetrievedChunk, ...]]:
    query = SearchQuery(
        text="How do I sample and configure the sampler?",
        top_k=4,
        library="pymc",
        library_version="6.1.0",
    )
    results = (
        make_result("chunk_a", rank=1, section=None, api_symbols=()),
        make_result(
            "chunk_b",
            rank=2,
            section="Parameters",
            api_symbols=("pymc.sample", "pymc.sampling.mcmc.sample"),
        ),
        make_result(
            "chunk_c",
            rank=3,
            section="Returns",
            api_symbols=("pymc.sample",),
        ),
        make_result(
            "chunk_d",
            rank=4,
            section="Notes",
            api_symbols=("pymc.sample",),
        ),
    )
    builder = RankedContextBuilder(TechnicalTokenizer())
    complete = builder.build(query, results, token_budget=100_000)
    two_item_budget = sum(item.token_count for item in complete.items[:2])
    context = builder.build(query, results, token_budget=two_item_budget)
    assert context.included_chunk_ids == ("chunk_a", "chunk_b")
    assert context.omitted_chunk_ids == ("chunk_c", "chunk_d")
    return context, results


def make_assessment(
    context: ConstructedContext,
    *,
    sufficiency: EvidenceSufficiency = EvidenceSufficiency.SUFFICIENT,
    context_chunk_ids: tuple[str, ...] | None = None,
    omitted_chunk_ids: tuple[str, ...] | None = None,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        policy_version="explicit-sufficient-test-stub-v1",
        sufficiency=sufficiency,
        should_abstain=sufficiency is not EvidenceSufficiency.SUFFICIENT,
        reason_codes=("synthetic_contract_test",),
        context_chunk_ids=(
            context.included_chunk_ids if context_chunk_ids is None else context_chunk_ids
        ),
        omitted_chunk_ids=(
            context.omitted_chunk_ids if omitted_chunk_ids is None else omitted_chunk_ids
        ),
    )


def make_generator_input(
    context: ConstructedContext,
    *,
    query: SearchQuery | None = None,
    assessment: EvidenceAssessment | None = None,
) -> GeneratorInput:
    return GeneratorInput(
        query=context.query if query is None else query,
        context=context,
        assessment=make_assessment(context) if assessment is None else assessment,
    )


def make_citation(source: ContextItem | Chunk, citation_id: str) -> Citation:
    return Citation(
        citation_id=citation_id,
        chunk_id=source.chunk_id,
        document_id=source.document_id,
        source_url=source.source_url,
        library=source.library,
        library_version=source.library_version,
        section=source.section,
        api_symbols=source.api_symbols,
    )


def make_answer(context: ConstructedContext) -> GroundedAnswer:
    citation_a = make_citation(context.items[0], "citation_a")
    citation_b = make_citation(context.items[1], "citation_b")
    return GroundedAnswer(
        is_abstaining=False,
        sections=(
            GroundedAnswerSection(
                section_id="sampling",
                heading="Sampling",
                claims=(
                    AtomicClaim(
                        claim_id="claim_a",
                        text="The first synthetic claim uses the first context item.",
                        citation_ids=("citation_a",),
                    ),
                    AtomicClaim(
                        claim_id="claim_b",
                        text="The second synthetic claim uses the second context item.",
                        citation_ids=("citation_b",),
                    ),
                ),
            ),
        ),
        citations=(citation_b, citation_a),
    )


def make_output() -> GeneratorOutput:
    context, _ = make_context()
    return GeneratorOutput(
        generator_input=make_generator_input(context),
        answer=make_answer(context),
    )


def test_generator_output_preserves_exact_citation_identity_and_round_trips_json() -> None:
    output = make_output()
    serialized = output.model_dump_json()
    restored = GeneratorOutput.model_validate_json(serialized)

    assert output.schema_version == "1"
    assert output.generator_input.schema_version == "1"
    assert output.answer.schema_version == "1"
    assert tuple(citation.chunk_id for citation in output.answer.citations) == (
        "chunk_b",
        "chunk_a",
    )
    for citation in output.answer.citations:
        item = next(
            item
            for item in output.generator_input.context.items
            if item.chunk_id == citation.chunk_id
        )
        assert citation.document_id == item.document_id
        assert citation.source_url == item.source_url
        assert citation.library == item.library
        assert citation.library_version == item.library_version
        assert citation.section == item.section
        assert citation.api_symbols == item.api_symbols
    assert restored == output
    assert restored.model_dump_json() == serialized


def test_generator_output_is_immutable() -> None:
    output = make_output()

    with pytest.raises(ValidationError, match="frozen"):
        output.answer = GroundedAnswer(is_abstaining=True)


def test_generator_output_accepts_a_clean_abstention_after_sufficient_input() -> None:
    context, _ = make_context()
    answer = GroundedAnswer(is_abstaining=True)

    output = GeneratorOutput(
        generator_input=make_generator_input(context),
        answer=answer,
    )

    assert output.answer.is_abstaining is True
    assert output.answer.sections == ()
    assert output.answer.citations == ()


def test_generator_output_accepts_an_answered_uncited_claim_for_later_evaluation() -> None:
    context, _ = make_context()
    claim = AtomicClaim(
        claim_id="uncited_claim",
        text="This claim deliberately has no citation.",
    )
    answer = GroundedAnswer(
        is_abstaining=False,
        sections=(
            GroundedAnswerSection(
                section_id="uncited",
                heading="Uncited claim",
                claims=(claim,),
            ),
        ),
    )

    output = GeneratorOutput(
        generator_input=make_generator_input(context),
        answer=answer,
    )

    assert output.answer.sections[0].claims[0].citation_ids == ()
    assert output.answer.citations == ()


def test_generator_output_accepts_one_citation_reused_by_multiple_claims() -> None:
    context, _ = make_context()
    citation = make_citation(context.items[0], "shared_citation")
    answer = GroundedAnswer(
        is_abstaining=False,
        sections=(
            GroundedAnswerSection(
                section_id="shared",
                heading="Shared evidence",
                claims=(
                    AtomicClaim(
                        claim_id="claim_a",
                        text="First claim.",
                        citation_ids=(citation.citation_id,),
                    ),
                    AtomicClaim(
                        claim_id="claim_b",
                        text="Second claim.",
                        citation_ids=(citation.citation_id,),
                    ),
                ),
            ),
        ),
        citations=(citation,),
    )

    output = GeneratorOutput(
        generator_input=make_generator_input(context),
        answer=answer,
    )

    assert tuple(claim.citation_ids for claim in output.answer.sections[0].claims) == (
        ("shared_citation",),
        ("shared_citation",),
    )


def test_generator_output_revalidates_unvalidated_nested_model_copies() -> None:
    output = make_output()
    section = output.answer.sections[0]
    invalid_claim = section.claims[0].model_copy(update={"text": ""})
    invalid_section = section.model_copy(update={"claims": (invalid_claim, *section.claims[1:])})
    invalid_answer = output.answer.model_copy(update={"sections": (invalid_section,)})

    with pytest.raises(ValidationError):
        GeneratorOutput(
            generator_input=output.generator_input,
            answer=invalid_answer,
        )


def test_atomic_claim_rejects_duplicate_citation_references() -> None:
    with pytest.raises(ValidationError, match="atomic claim citation IDs must be unique"):
        AtomicClaim(
            claim_id="claim",
            text="Claim text.",
            citation_ids=("citation_a", "citation_a"),
        )


def test_grounded_answer_section_requires_at_least_one_claim() -> None:
    with pytest.raises(ValidationError, match="at least 1 item"):
        GroundedAnswerSection(
            section_id="empty",
            heading="Empty",
            claims=(),
        )


def test_grounded_answer_section_forbids_untracked_body_prose() -> None:
    claim = AtomicClaim(claim_id="claim", text="Claim text.")

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        GroundedAnswerSection.model_validate(
            {
                "section_id": "section",
                "heading": "Heading",
                "claims": (claim,),
                "body": "Free-form factual prose is not part of the contract.",
            }
        )


def test_grounded_answer_forbids_untracked_answer_text() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        GroundedAnswer.model_validate(
            {
                "is_abstaining": True,
                "text": "Free-form answer text is not part of the contract.",
            }
        )


@pytest.mark.parametrize("payload", ["sections", "citations"])
def test_grounded_answer_rejects_content_on_an_abstention(payload: str) -> None:
    context, _ = make_context()
    values: dict[str, object] = {"is_abstaining": True}
    if payload == "sections":
        values["sections"] = (
            GroundedAnswerSection(
                section_id="section",
                heading="Heading",
                claims=(AtomicClaim(claim_id="claim", text="Claim text."),),
            ),
        )
    else:
        values["citations"] = (make_citation(context.items[0], "citation"),)

    with pytest.raises(ValidationError, match="abstaining answers must not contain"):
        GroundedAnswer.model_validate(values)


def test_grounded_answer_requires_a_section_when_not_abstaining() -> None:
    with pytest.raises(ValidationError, match="must contain at least one section"):
        GroundedAnswer(is_abstaining=False)


def test_grounded_answer_requires_strict_abstention_boolean() -> None:
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate({"is_abstaining": 1})


def test_grounded_answer_rejects_duplicate_citation_ids() -> None:
    context, _ = make_context()
    citation_a = make_citation(context.items[0], "duplicate")
    citation_b = make_citation(context.items[1], "duplicate")
    section = GroundedAnswerSection(
        section_id="section",
        heading="Heading",
        claims=(
            AtomicClaim(
                claim_id="claim",
                text="Claim text.",
                citation_ids=("duplicate",),
            ),
        ),
    )

    with pytest.raises(ValidationError, match="citation IDs must be unique"):
        GroundedAnswer(
            is_abstaining=False,
            sections=(section,),
            citations=(citation_a, citation_b),
        )


def test_grounded_answer_rejects_multiple_citation_aliases_for_one_chunk() -> None:
    context, _ = make_context()
    citation_a = make_citation(context.items[0], "citation_a")
    citation_alias = make_citation(context.items[0], "citation_alias")
    section = GroundedAnswerSection(
        section_id="section",
        heading="Heading",
        claims=(
            AtomicClaim(
                claim_id="claim",
                text="Claim text.",
                citation_ids=("citation_a", "citation_alias"),
            ),
        ),
    )

    with pytest.raises(ValidationError, match="cited chunk IDs must be unique"):
        GroundedAnswer(
            is_abstaining=False,
            sections=(section,),
            citations=(citation_a, citation_alias),
        )


def test_grounded_answer_rejects_unreferenced_registry_citations() -> None:
    context, _ = make_context()
    used = make_citation(context.items[0], "used")
    orphan = make_citation(context.items[1], "orphan")
    section = GroundedAnswerSection(
        section_id="section",
        heading="Heading",
        claims=(
            AtomicClaim(
                claim_id="claim",
                text="Claim text.",
                citation_ids=("used",),
            ),
        ),
    )

    with pytest.raises(ValidationError, match="unreferenced citation IDs: orphan"):
        GroundedAnswer(
            is_abstaining=False,
            sections=(section,),
            citations=(used, orphan),
        )


def test_grounded_answer_rejects_duplicate_section_ids() -> None:
    sections = (
        GroundedAnswerSection(
            section_id="duplicate",
            heading="First",
            claims=(AtomicClaim(claim_id="claim_a", text="First claim."),),
        ),
        GroundedAnswerSection(
            section_id="duplicate",
            heading="Second",
            claims=(AtomicClaim(claim_id="claim_b", text="Second claim."),),
        ),
    )

    with pytest.raises(ValidationError, match="section IDs must be unique"):
        GroundedAnswer(is_abstaining=False, sections=sections)


def test_grounded_answer_rejects_duplicate_claim_ids_across_sections() -> None:
    sections = (
        GroundedAnswerSection(
            section_id="first",
            heading="First",
            claims=(AtomicClaim(claim_id="duplicate", text="First claim."),),
        ),
        GroundedAnswerSection(
            section_id="second",
            heading="Second",
            claims=(AtomicClaim(claim_id="duplicate", text="Second claim."),),
        ),
    )

    with pytest.raises(ValidationError, match="claim IDs must be unique"):
        GroundedAnswer(is_abstaining=False, sections=sections)


def test_grounded_answer_rejects_an_unknown_claim_citation_reference() -> None:
    section = GroundedAnswerSection(
        section_id="section",
        heading="Heading",
        claims=(
            AtomicClaim(
                claim_id="claim",
                text="Claim text.",
                citation_ids=("unknown",),
            ),
        ),
    )

    with pytest.raises(ValidationError, match="references unknown citation IDs: unknown"):
        GroundedAnswer(is_abstaining=False, sections=(section,))


def test_generator_input_rejects_a_query_that_differs_from_the_context() -> None:
    context, _ = make_context()
    different_query = SearchQuery(
        text="A different query",
        top_k=4,
        library="pymc",
        library_version="6.1.0",
    )

    with pytest.raises(ValidationError, match="query must exactly match"):
        make_generator_input(context, query=different_query)


@pytest.mark.parametrize(
    ("assessment_field", "replacement"),
    [
        ("context_chunk_ids", ("chunk_a",)),
        ("context_chunk_ids", ("chunk_b", "chunk_a")),
        ("context_chunk_ids", ("chunk_a", "chunk_b", "chunk_extra")),
        ("omitted_chunk_ids", ("chunk_c",)),
        ("omitted_chunk_ids", ("chunk_d", "chunk_c")),
        ("omitted_chunk_ids", ("chunk_c", "chunk_d", "chunk_extra")),
    ],
)
def test_generator_input_requires_exact_ordered_assessment_chunk_ids(
    assessment_field: str,
    replacement: tuple[str, ...],
) -> None:
    context, _ = make_context()
    if assessment_field == "context_chunk_ids":
        assessment = make_assessment(context, context_chunk_ids=replacement)
    else:
        assessment = make_assessment(context, omitted_chunk_ids=replacement)
    expected_message = (
        "assessment context chunk IDs must exactly match"
        if assessment_field == "context_chunk_ids"
        else "assessment omitted chunk IDs must exactly match"
    )

    with pytest.raises(ValidationError, match=expected_message):
        make_generator_input(context, assessment=assessment)


@pytest.mark.parametrize(
    "sufficiency",
    [EvidenceSufficiency.INSUFFICIENT, EvidenceSufficiency.NOT_ASSESSED],
)
def test_generator_input_rejects_any_assessment_without_explicit_sufficiency(
    sufficiency: EvidenceSufficiency,
) -> None:
    context, _ = make_context()
    assessment = make_assessment(context, sufficiency=sufficiency)

    with pytest.raises(ValidationError, match="requires an explicitly sufficient"):
        make_generator_input(context, assessment=assessment)


def test_generator_output_rejects_a_citation_to_an_omitted_chunk() -> None:
    context, results = make_context()
    citation = make_citation(results[2].chunk, "citation_omitted")
    answer = GroundedAnswer(
        is_abstaining=False,
        sections=(
            GroundedAnswerSection(
                section_id="section",
                heading="Heading",
                claims=(
                    AtomicClaim(
                        claim_id="claim",
                        text="Claim text.",
                        citation_ids=(citation.citation_id,),
                    ),
                ),
            ),
        ),
        citations=(citation,),
    )

    with pytest.raises(ValidationError, match="references omitted chunk chunk_c"):
        GeneratorOutput(
            generator_input=make_generator_input(context),
            answer=answer,
        )


def test_generator_output_rejects_a_citation_to_an_unknown_chunk() -> None:
    context, _ = make_context()
    citation_values = make_citation(context.items[0], "citation_unknown").model_dump(mode="python")
    citation_values["chunk_id"] = "chunk_unknown"
    citation = Citation.model_validate(citation_values)
    answer = GroundedAnswer(
        is_abstaining=False,
        sections=(
            GroundedAnswerSection(
                section_id="section",
                heading="Heading",
                claims=(
                    AtomicClaim(
                        claim_id="claim",
                        text="Claim text.",
                        citation_ids=(citation.citation_id,),
                    ),
                ),
            ),
        ),
        citations=(citation,),
    )

    with pytest.raises(ValidationError, match="must resolve to an included context item"):
        GeneratorOutput(
            generator_input=make_generator_input(context),
            answer=answer,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("document_id", "wrong_document"),
        ("source_url", "https://docs.example.test/wrong.html"),
        ("library", "arviz"),
        ("library_version", "0.0.0"),
        ("section", "Wrong section"),
        ("api_symbols", ("pymc.sampling.mcmc.sample", "pymc.sample")),
    ],
)
def test_generator_output_rejects_every_citation_provenance_mismatch(
    field: str,
    replacement: object,
) -> None:
    context, _ = make_context()
    citation_a = make_citation(context.items[0], "citation_a")
    citation_b_values = make_citation(context.items[1], "citation_b").model_dump(mode="python")
    citation_b_values[field] = replacement
    citation_b = Citation.model_validate(citation_b_values)
    answer = GroundedAnswer(
        is_abstaining=False,
        sections=(
            GroundedAnswerSection(
                section_id="section",
                heading="Heading",
                claims=(
                    AtomicClaim(
                        claim_id="claim",
                        text="Claim text.",
                        citation_ids=("citation_a", "citation_b"),
                    ),
                ),
            ),
        ),
        citations=(citation_a, citation_b),
    )

    with pytest.raises(ValidationError, match=field):
        GeneratorOutput(
            generator_input=make_generator_input(context),
            answer=answer,
        )


@pytest.mark.parametrize("contract", ["answer", "input", "output"])
def test_versioned_grounding_contracts_reject_unknown_schema_versions(contract: str) -> None:
    output = make_output()

    with pytest.raises(ValidationError):
        if contract == "answer":
            values = output.answer.model_dump(mode="python")
            values["schema_version"] = "2"
            GroundedAnswer.model_validate(values)
        elif contract == "input":
            values = output.generator_input.model_dump(mode="python")
            values["schema_version"] = "2"
            GeneratorInput.model_validate(values)
        else:
            values = output.model_dump(mode="python")
            values["schema_version"] = "2"
            GeneratorOutput.model_validate(values)
