"""Validated domain models shared by ingestion and retrieval components."""

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import (
    AnyUrl,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    StringConstraints,
    model_validator,
)

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
RenderedText = Annotated[str, StringConstraints(min_length=1)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class SourceType(StrEnum):
    """Supported source structures for parsing and chunking policies."""

    API_REFERENCE = "api_reference"
    CONCEPTUAL_GUIDE = "conceptual_guide"
    TUTORIAL = "tutorial"
    EXAMPLE = "example"
    NOTEBOOK = "notebook"
    REPOSITORY_CODE = "repository_code"
    PROJECT_NOTE = "project_note"
    TRACEBACK = "traceback"


class Difficulty(StrEnum):
    """Pedagogical difficulty assigned to a chunk when known."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EvidenceSufficiency(StrEnum):
    """Whether available context has been assessed as sufficient for answering."""

    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    NOT_ASSESSED = "not_assessed"


class DomainModel(BaseModel):
    """Strict and immutable base for values crossing component boundaries."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        revalidate_instances="always",
    )


class SourceManifest(DomainModel):
    """Provenance and integrity metadata for one acquired source artifact."""

    manifest_version: NonEmptyString = "1"
    source_id: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    source_type: SourceType
    source_url: AnyUrl
    release_tag: NonEmptyString | None = None
    release_url: AnyUrl | None = None
    source_commit: NonEmptyString | None = None
    source_last_modified_at: AwareDatetime | None = None
    downloaded_at: AwareDatetime
    content_hash: Sha256
    media_type: NonEmptyString
    expected_api_symbol: NonEmptyString | None = None
    source_path: NonEmptyString | None = None
    license_name: NonEmptyString
    license_url: AnyUrl

    @model_validator(mode="after")
    def source_contract_matches_type(self) -> Self:
        """Require provenance fields needed by each supported source type."""
        if self.source_type is SourceType.API_REFERENCE and self.expected_api_symbol is None:
            msg = "expected_api_symbol is required for API reference sources"
            raise ValueError(msg)
        if self.source_type is SourceType.REPOSITORY_CODE:
            if self.expected_api_symbol is None:
                msg = "expected_api_symbol is required for repository code sources"
                raise ValueError(msg)
            if self.source_commit is None:
                msg = "source_commit is required for repository code sources"
                raise ValueError(msg)
            if self.source_path is None:
                msg = "source_path is required for repository code sources"
                raise ValueError(msg)
            source_path = PurePosixPath(self.source_path)
            if source_path.is_absolute() or ".." in source_path.parts:
                msg = "source_path must be a relative repository path without parent traversal"
                raise ValueError(msg)
        if self.source_type is SourceType.NOTEBOOK:
            if self.source_commit is None:
                msg = "source_commit is required for notebook sources"
                raise ValueError(msg)
            if self.source_path is None:
                msg = "source_path is required for notebook sources"
                raise ValueError(msg)
            source_path = PurePosixPath(self.source_path)
            if source_path.is_absolute() or ".." in source_path.parts:
                msg = "source_path must be a relative repository path without parent traversal"
                raise ValueError(msg)
        return self


class Document(DomainModel):
    """A normalized source document with reproducible provenance."""

    document_id: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    source_type: SourceType
    source_url: AnyUrl
    title: NonEmptyString
    content: NonEmptyString
    content_hash: Sha256
    language: NonEmptyString = "en"
    fetched_at: AwareDatetime
    source_commit: NonEmptyString | None = None
    license_name: NonEmptyString | None = None
    license_url: AnyUrl | None = None
    parser_version: NonEmptyString | None = None


class Chunk(DomainModel):
    """A structure-aware retrieval unit linked to its source document."""

    chunk_id: NonEmptyString
    document_id: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    source_type: SourceType
    source_url: AnyUrl
    title: NonEmptyString
    section: NonEmptyString | None = None
    content: NonEmptyString
    content_hash: Sha256
    api_symbols: tuple[NonEmptyString, ...] = ()
    concepts: tuple[NonEmptyString, ...] = ()
    difficulty: Difficulty | None = None
    prerequisites: tuple[NonEmptyString, ...] = ()
    contains_code: bool = False
    language: NonEmptyString = "en"
    created_at: AwareDatetime
    indexed_at: AwareDatetime | None = None
    chunker_version: NonEmptyString | None = None

    @model_validator(mode="after")
    def indexed_at_must_follow_creation(self) -> Self:
        """Reject chronologically inconsistent indexing metadata."""
        if self.indexed_at is not None and self.indexed_at < self.created_at:
            msg = "indexed_at must not be earlier than created_at"
            raise ValueError(msg)
        return self


class SearchQuery(DomainModel):
    """A retrieval request and its explicit metadata filters."""

    text: NonEmptyString
    top_k: int = Field(default=10, ge=1, le=100)
    library: NonEmptyString | None = None
    library_version: NonEmptyString | None = None
    source_types: tuple[SourceType, ...] = ()
    api_symbols: tuple[NonEmptyString, ...] = ()


class RetrievedChunk(DomainModel):
    """A ranked chunk returned by a named retrieval strategy."""

    chunk: Chunk
    score: FiniteFloat
    rank: int = Field(ge=1)
    retriever: NonEmptyString


def render_context_item_v1(
    *,
    position: int,
    retrieval_rank: int,
    retriever: str,
    chunk_id: str,
    document_id: str,
    source_url: AnyUrl,
    library: str,
    library_version: str,
    source_type: SourceType,
    title: str,
    section: str | None,
    api_symbols: tuple[str, ...],
    content: str,
) -> str:
    """Render the canonical, provider-neutral context item representation."""
    rendered_api_symbols = ", ".join(api_symbols) if api_symbols else "None"
    rendered_section = section if section is not None else "Unsectioned"
    return "\n".join(
        (
            f"Context item: {position}",
            f"Retrieval rank: {retrieval_rank}",
            f"Retrieval strategy: {retriever}",
            f"Chunk ID: {chunk_id}",
            f"Document ID: {document_id}",
            f"Source URL: {source_url}",
            f"Library: {library}",
            f"Library version: {library_version}",
            f"Source type: {source_type.value}",
            f"Title: {title}",
            f"Section: {rendered_section}",
            f"API symbols: {rendered_api_symbols}",
            "",
            "Content:",
            content,
        )
    )


class ContextItem(DomainModel):
    """One complete ranked evidence item admitted to a constructed context."""

    position: int = Field(ge=1, strict=True)
    retrieval_rank: int = Field(ge=1, strict=True)
    retriever: NonEmptyString
    chunk_id: NonEmptyString
    document_id: NonEmptyString
    library: NonEmptyString
    library_version: NonEmptyString
    source_type: SourceType
    source_url: AnyUrl
    title: NonEmptyString
    section: NonEmptyString | None = None
    api_symbols: tuple[NonEmptyString, ...] = ()
    content: NonEmptyString
    rendered_text: RenderedText
    token_count: int = Field(gt=0, strict=True)

    @model_validator(mode="after")
    def rendered_text_matches_structured_evidence(self) -> Self:
        """Reject context text that diverges from its structured provenance and content."""
        expected = render_context_item_v1(
            position=self.position,
            retrieval_rank=self.retrieval_rank,
            retriever=self.retriever,
            chunk_id=self.chunk_id,
            document_id=self.document_id,
            source_url=self.source_url,
            library=self.library,
            library_version=self.library_version,
            source_type=self.source_type,
            title=self.title,
            section=self.section,
            api_symbols=self.api_symbols,
            content=self.content,
        )
        if self.rendered_text != expected:
            msg = "rendered_text must match the canonical context-item-text-v1 representation"
            raise ValueError(msg)
        return self


class ConstructedContext(DomainModel):
    """A deterministic, budget-bounded sequence of traceable evidence items."""

    schema_version: Literal["1"] = "1"
    builder_version: NonEmptyString
    rendering_policy: Literal["context-item-text-v1"]
    truncation_policy: Literal["rank-prefix-whole-item-v1"]
    query: SearchQuery
    token_counter: NonEmptyString
    token_budget: int = Field(gt=0, strict=True)
    used_tokens: int = Field(ge=0, strict=True)
    items: tuple[ContextItem, ...] = ()
    included_chunk_ids: tuple[NonEmptyString, ...] = ()
    omitted_chunk_ids: tuple[NonEmptyString, ...] = ()

    @model_validator(mode="after")
    def validate_accounting_and_identity(self) -> Self:
        """Require canonical item identity and internally consistent token accounting."""
        expected_positions = tuple(range(1, len(self.items) + 1))
        positions = tuple(item.position for item in self.items)
        if positions != expected_positions:
            msg = "context item positions must be contiguous and start at one"
            raise ValueError(msg)

        canonical_order = tuple(
            sorted(self.items, key=lambda item: (item.retrieval_rank, item.chunk_id))
        )
        if self.items != canonical_order:
            msg = "context items must be ordered by retrieval_rank and chunk_id"
            raise ValueError(msg)

        item_ids = tuple(item.chunk_id for item in self.items)
        if self.included_chunk_ids != item_ids:
            msg = "included_chunk_ids must match context items in order"
            raise ValueError(msg)
        if len(set(item_ids)) != len(item_ids):
            msg = "context item chunk IDs must be unique"
            raise ValueError(msg)
        if len(set(self.omitted_chunk_ids)) != len(self.omitted_chunk_ids):
            msg = "omitted_chunk_ids must be unique"
            raise ValueError(msg)
        if set(item_ids) & set(self.omitted_chunk_ids):
            msg = "included and omitted chunk IDs must not overlap"
            raise ValueError(msg)

        expected_used_tokens = sum(item.token_count for item in self.items)
        if self.used_tokens != expected_used_tokens:
            msg = "used_tokens must equal the sum of context item token counts"
            raise ValueError(msg)
        if self.used_tokens > self.token_budget:
            msg = "used_tokens must not exceed token_budget"
            raise ValueError(msg)
        return self


class EvidenceAssessment(DomainModel):
    """A deterministic policy decision over traceable context chunk identities."""

    schema_version: Literal["1"] = "1"
    policy_version: NonEmptyString
    sufficiency: EvidenceSufficiency
    should_abstain: bool = Field(strict=True)
    reason_codes: tuple[NonEmptyString, ...] = Field(min_length=1)
    context_chunk_ids: tuple[NonEmptyString, ...] = ()
    omitted_chunk_ids: tuple[NonEmptyString, ...] = ()

    @model_validator(mode="after")
    def validate_decision_and_traceability(self) -> Self:
        """Require consistent abstention semantics and deterministic identity tuples."""
        expected_abstention = self.sufficiency is not EvidenceSufficiency.SUFFICIENT
        if self.should_abstain is not expected_abstention:
            msg = "should_abstain must be true unless evidence sufficiency is sufficient"
            raise ValueError(msg)

        requires_context = self.sufficiency in {
            EvidenceSufficiency.SUFFICIENT,
            EvidenceSufficiency.NOT_ASSESSED,
        }
        if requires_context and not self.context_chunk_ids:
            msg = "sufficient and not_assessed decisions require context chunk IDs"
            raise ValueError(msg)

        if len(set(self.reason_codes)) != len(self.reason_codes):
            msg = "evidence assessment reason codes must be unique"
            raise ValueError(msg)
        if self.reason_codes != tuple(sorted(self.reason_codes)):
            msg = "evidence assessment reason codes must be lexicographically ordered"
            raise ValueError(msg)

        if len(set(self.context_chunk_ids)) != len(self.context_chunk_ids):
            msg = "evidence assessment context chunk IDs must be unique"
            raise ValueError(msg)
        if len(set(self.omitted_chunk_ids)) != len(self.omitted_chunk_ids):
            msg = "evidence assessment omitted chunk IDs must be unique"
            raise ValueError(msg)
        if set(self.context_chunk_ids) & set(self.omitted_chunk_ids):
            msg = "evidence assessment context and omitted chunk IDs must not overlap"
            raise ValueError(msg)
        return self


class Citation(DomainModel):
    """A traceable reference to one complete item in the supplied context."""

    citation_id: NonEmptyString
    chunk_id: NonEmptyString
    document_id: NonEmptyString
    source_url: AnyUrl
    library: NonEmptyString
    library_version: NonEmptyString
    section: NonEmptyString | None = None
    api_symbols: tuple[NonEmptyString, ...] = ()


class AtomicClaim(DomainModel):
    """One independently assessable answer claim and its citation references."""

    claim_id: NonEmptyString
    text: NonEmptyString
    citation_ids: tuple[NonEmptyString, ...] = ()

    @model_validator(mode="after")
    def citation_references_must_be_unique(self) -> Self:
        """Reject duplicate references while permitting measurable uncited claims."""
        if len(set(self.citation_ids)) != len(self.citation_ids):
            msg = "atomic claim citation IDs must be unique"
            raise ValueError(msg)
        return self


class GroundedAnswerSection(DomainModel):
    """An ordered group of atomic claims with a non-factual organizational label."""

    section_id: NonEmptyString
    heading: NonEmptyString = Field(
        description=(
            "Organizational metadata only; consumers must not treat it as factual answer content."
        )
    )
    claims: tuple[AtomicClaim, ...] = Field(min_length=1)


class GroundedAnswer(DomainModel):
    """A structured answer or an explicit claim-free abstention."""

    schema_version: Literal["1"] = "1"
    is_abstaining: bool = Field(strict=True)
    sections: tuple[GroundedAnswerSection, ...] = ()
    citations: tuple[Citation, ...] = ()

    @model_validator(mode="after")
    def validate_structure_and_references(self) -> Self:
        """Require unique identities, resolved references, and empty abstentions."""
        if self.is_abstaining:
            if self.sections or self.citations:
                msg = "abstaining answers must not contain sections, claims, or citations"
                raise ValueError(msg)
            return self

        if not self.sections:
            msg = "non-abstaining answers must contain at least one section"
            raise ValueError(msg)

        section_ids = tuple(section.section_id for section in self.sections)
        if len(set(section_ids)) != len(section_ids):
            msg = "grounded answer section IDs must be unique"
            raise ValueError(msg)

        claims = tuple(claim for section in self.sections for claim in section.claims)
        claim_ids = tuple(claim.claim_id for claim in claims)
        if len(set(claim_ids)) != len(claim_ids):
            msg = "grounded answer claim IDs must be unique"
            raise ValueError(msg)

        citation_ids = tuple(citation.citation_id for citation in self.citations)
        if len(set(citation_ids)) != len(citation_ids):
            msg = "grounded answer citation IDs must be unique"
            raise ValueError(msg)

        cited_chunk_ids = tuple(citation.chunk_id for citation in self.citations)
        if len(set(cited_chunk_ids)) != len(cited_chunk_ids):
            msg = "grounded answer cited chunk IDs must be unique"
            raise ValueError(msg)

        known_citation_ids = set(citation_ids)
        referenced_citation_ids: set[str] = set()
        for claim in claims:
            referenced_citation_ids.update(claim.citation_ids)
            unknown_ids = tuple(
                citation_id
                for citation_id in claim.citation_ids
                if citation_id not in known_citation_ids
            )
            if unknown_ids:
                rendered_ids = ", ".join(unknown_ids)
                msg = f"claim {claim.claim_id} references unknown citation IDs: {rendered_ids}"
                raise ValueError(msg)

        orphan_ids = tuple(
            citation_id
            for citation_id in citation_ids
            if citation_id not in referenced_citation_ids
        )
        if orphan_ids:
            rendered_ids = ", ".join(orphan_ids)
            msg = f"grounded answer contains unreferenced citation IDs: {rendered_ids}"
            raise ValueError(msg)
        return self


class GeneratorInput(DomainModel):
    """Evidence and policy decision that explicitly authorize grounded generation."""

    schema_version: Literal["1"] = "1"
    query: SearchQuery
    context: ConstructedContext
    assessment: EvidenceAssessment

    @model_validator(mode="after")
    def validate_generation_authorization(self) -> Self:
        """Bind the assessment to the context and require explicit sufficiency."""
        if self.query != self.context.query:
            msg = "generator input query must exactly match the constructed context query"
            raise ValueError(msg)
        if self.assessment.context_chunk_ids != self.context.included_chunk_ids:
            msg = "assessment context chunk IDs must exactly match the constructed context"
            raise ValueError(msg)
        if self.assessment.omitted_chunk_ids != self.context.omitted_chunk_ids:
            msg = "assessment omitted chunk IDs must exactly match the constructed context"
            raise ValueError(msg)
        if (
            self.assessment.sufficiency is not EvidenceSufficiency.SUFFICIENT
            or self.assessment.should_abstain
        ):
            msg = "generator input requires an explicitly sufficient non-abstaining assessment"
            raise ValueError(msg)
        return self


class GeneratorOutput(DomainModel):
    """A grounded answer validated against the exact evidence supplied for generation."""

    schema_version: Literal["1"] = "1"
    generator_input: GeneratorInput
    answer: GroundedAnswer

    @model_validator(mode="after")
    def citations_must_match_included_context(self) -> Self:
        """Resolve citations only to included items with identical provenance."""
        context = self.generator_input.context
        items_by_chunk_id = {item.chunk_id: item for item in context.items}
        omitted_chunk_ids = set(context.omitted_chunk_ids)
        provenance_fields = (
            "document_id",
            "source_url",
            "library",
            "library_version",
            "section",
            "api_symbols",
        )

        for citation in self.answer.citations:
            if citation.chunk_id in omitted_chunk_ids:
                msg = (
                    f"citation {citation.citation_id} references omitted chunk {citation.chunk_id}"
                )
                raise ValueError(msg)

            context_item = items_by_chunk_id.get(citation.chunk_id)
            if context_item is None:
                msg = f"citation {citation.citation_id} must resolve to an included context item"
                raise ValueError(msg)

            mismatched_fields = tuple(
                field
                for field in provenance_fields
                if getattr(citation, field) != getattr(context_item, field)
            )
            if mismatched_fields:
                rendered_fields = ", ".join(mismatched_fields)
                msg = (
                    f"citation {citation.citation_id} provenance does not match included "
                    f"context item {citation.chunk_id}: {rendered_fields}"
                )
                raise ValueError(msg)
        return self
