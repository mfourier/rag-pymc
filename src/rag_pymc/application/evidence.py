"""Project-owned use case for deterministic, read-only evidence inspection."""

from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Annotated, Literal, Self
from unicodedata import category, normalize

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    StringConstraints,
    field_validator,
    model_validator,
)

from rag_pymc.abstention.protocols import AbstentionPolicy
from rag_pymc.context.protocols import ContextBuilder
from rag_pymc.domain import (
    Chunk,
    ConstructedContext,
    Document,
    EvidenceAssessment,
    EvidenceSufficiency,
    RetrievedChunk,
    SearchQuery,
    SourceType,
)
from rag_pymc.retrieval.protocols import Retriever
from rag_pymc.serialization import canonical_json_sha256

MAX_EVIDENCE_QUERY_CHARACTERS = 1_000
MAX_EVIDENCE_TOP_K = 10
MAX_EVIDENCE_TOKEN_BUDGET = 8_192
CONTEXT_RETRIEVAL_TOP_K = 3

NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
ChunkId = Annotated[str, StringConstraints(pattern=r"^chunk_[a-f0-9]{20}$")]


class EvidenceModel(BaseModel):
    """Strict immutable base for values crossing the evidence-service boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class SearchEvidenceRequest(EvidenceModel):
    """Bounded request for deterministic evidence retrieval."""

    query: str = Field(min_length=1, max_length=MAX_EVIDENCE_QUERY_CHARACTERS, strict=True)
    version: Literal["6.2.0"]
    top_k: int = Field(ge=1, le=MAX_EVIDENCE_TOP_K, strict=True)

    @field_validator("query", mode="before")
    @classmethod
    def normalize_query(cls, value: object) -> object:
        """Normalize Unicode and whitespace without accepting hidden control characters."""
        return _normalize_query(value)


class InspectEvidenceContextRequest(EvidenceModel):
    """Bounded request for context construction and sufficiency inspection."""

    query: str = Field(min_length=1, max_length=MAX_EVIDENCE_QUERY_CHARACTERS, strict=True)
    version: Literal["6.2.0"]
    token_budget: int = Field(ge=1, le=MAX_EVIDENCE_TOKEN_BUDGET, strict=True)

    @field_validator("query", mode="before")
    @classmethod
    def normalize_query(cls, value: object) -> object:
        """Apply the same query policy used by evidence search."""
        return _normalize_query(value)


class GetEvidenceChunkRequest(EvidenceModel):
    """Resolve one opaque chunk identity inside the authorized corpus only."""

    chunk_id: ChunkId
    version: Literal["6.2.0"]


class Bm25Parameters(EvidenceModel):
    """Exact selected BM25 configuration."""

    k1: FiniteFloat = Field(gt=0)
    b: FiniteFloat = Field(ge=0, le=1)


class AuthorizedCorpusMetadata(EvidenceModel):
    """Provenance-complete identity of the only corpus admitted by a service."""

    schema_version: Literal["1"] = "1"
    corpus_id: NonEmptyString
    corpus_hash_policy: Literal["canonical-corpus-provenance-json-v2"]
    corpus_sha256: Sha256
    legacy_content_hash_policy: Literal["canonical-chunk-identity-json-v1"]
    legacy_content_sha256: Sha256
    library: Literal["pymc"]
    library_version: Literal["6.2.0"]
    source_type: Literal["api_reference"] = "api_reference"
    release_tag: Literal["v6.2.0"]
    source_commit: NonEmptyString
    document_count: int = Field(ge=1, strict=True)
    chunk_count: int = Field(ge=1, strict=True)
    retriever: Literal["bm25-v1"]
    tokenizer: Literal["technical-v1"]
    bm25: Bm25Parameters
    limitations: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_canonical_limitations(self) -> Self:
        """Keep repeated calls byte-stable and limitation-complete."""
        if self.limitations != tuple(sorted(set(self.limitations))):
            raise ValueError("authorized corpus limitations must be unique and ordered")
        return self


class EvidenceProvenance(EvidenceModel):
    """Document-level provenance attached to every authorized evidence chunk."""

    document_id: NonEmptyString
    document_content_sha256: Sha256
    source_url: AnyUrl
    source_commit: NonEmptyString
    license_name: NonEmptyString
    license_url: AnyUrl
    parser_version: NonEmptyString
    chunker_version: NonEmptyString

    @model_validator(mode="after")
    def require_official_pymc_source(self) -> Self:
        """Prevent a structurally valid URL from crossing the official-source boundary."""
        source_url = str(self.source_url)
        if not source_url.startswith("https://www.pymc.io/projects/docs/"):
            raise ValueError("evidence source URL must be official HTTPS PyMC documentation")
        return self


class AuthorizedEvidenceChunk(EvidenceModel):
    """Exact authorized text and provenance returned from the controlled corpus."""

    chunk_id: ChunkId
    rank: int | None = Field(default=None, ge=1, strict=True)
    score: FiniteFloat | None = None
    title: NonEmptyString
    section: NonEmptyString | None = None
    api_symbols: tuple[NonEmptyString, ...]
    library: Literal["pymc"]
    library_version: Literal["6.2.0"]
    source_type: Literal["api_reference"]
    content_sha256: Sha256
    text: NonEmptyString
    provenance: EvidenceProvenance

    @model_validator(mode="after")
    def require_rank_and_score_together(self) -> Self:
        """Distinguish ranked retrieval results from direct chunk lookup."""
        if (self.rank is None) is not (self.score is None):
            raise ValueError(
                "evidence rank and score must either both be present or both be absent"
            )
        return self


class EvidenceAuthorization(EvidenceModel):
    """Fail-closed statement about whether evidence may enter generation."""

    schema_version: Literal["1"] = "1"
    policy_version: NonEmptyString
    sufficiency: EvidenceSufficiency
    should_abstain: Literal[True] = True
    generation_permitted: Literal[False] = False
    reason_codes: tuple[NonEmptyString, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_fail_closed_state(self) -> Self:
        """Forbid a positive result from this evidence-only service."""
        if self.sufficiency is EvidenceSufficiency.SUFFICIENT:
            raise ValueError("evidence-only authorization cannot report sufficient evidence")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ValueError("authorization reason codes must be unique and ordered")
        return self


class SearchEvidenceResult(EvidenceModel):
    """Versioned deterministic evidence-search result."""

    schema_version: Literal["search-pymc-evidence-v1"] = "search-pymc-evidence-v1"
    service_version: Literal["pymc-evidence-inspection-v1"] = "pymc-evidence-inspection-v1"
    query_normalization: Literal["unicode-nfkc-whitespace-v1"] = "unicode-nfkc-whitespace-v1"
    query_hash_policy: Literal["normalized-query-utf8-sha256-v1"] = (
        "normalized-query-utf8-sha256-v1"
    )
    normalized_query: NonEmptyString
    query_sha256: Sha256
    requested_top_k: int = Field(ge=1, le=MAX_EVIDENCE_TOP_K, strict=True)
    corpus: AuthorizedCorpusMetadata
    chunk_ids: tuple[ChunkId, ...]
    results: tuple[AuthorizedEvidenceChunk, ...]
    authorization: EvidenceAuthorization

    @model_validator(mode="after")
    def require_result_identity(self) -> Self:
        """Bind the identity projection to the exact stable result order."""
        if self.query_sha256 != _hash_normalized_query(self.normalized_query):
            raise ValueError("search query hash does not match its normalized query")
        if self.chunk_ids != tuple(result.chunk_id for result in self.results):
            raise ValueError("search chunk IDs must match results in order")
        expected_ranks = tuple(range(1, len(self.results) + 1))
        if tuple(result.rank for result in self.results) != expected_ranks:
            raise ValueError("search result ranks must be contiguous and start at one")
        return self


class InspectEvidenceContextResult(EvidenceModel):
    """Versioned constructed context with an exact conservative assessment."""

    schema_version: Literal["inspect-pymc-context-v1"] = "inspect-pymc-context-v1"
    service_version: Literal["pymc-evidence-inspection-v1"] = "pymc-evidence-inspection-v1"
    query_normalization: Literal["unicode-nfkc-whitespace-v1"] = "unicode-nfkc-whitespace-v1"
    query_hash_policy: Literal["normalized-query-utf8-sha256-v1"] = (
        "normalized-query-utf8-sha256-v1"
    )
    normalized_query: NonEmptyString
    query_sha256: Sha256
    corpus: AuthorizedCorpusMetadata
    context_hash_policy: Literal["canonical-constructed-context-json-v1"] = (
        "canonical-constructed-context-json-v1"
    )
    context_sha256: Sha256
    context: ConstructedContext
    evidence: tuple[AuthorizedEvidenceChunk, ...]
    assessment: EvidenceAssessment
    authorization: EvidenceAuthorization

    @model_validator(mode="after")
    def require_context_identity_and_assessment(self) -> Self:
        """Bind text, hash, policy decision, and authorized evidence to one context."""
        if self.query_sha256 != _hash_normalized_query(self.normalized_query):
            raise ValueError("context query hash does not match its normalized query")
        expected_hash = canonical_json_sha256(self.context.model_dump(mode="json"))
        if self.context_sha256 != expected_hash:
            raise ValueError("context SHA-256 must match canonical context JSON")
        if self.context.query.text != self.normalized_query:
            raise ValueError("context query must match the normalized request")
        if tuple(item.chunk_id for item in self.evidence) != self.context.included_chunk_ids:
            raise ValueError("context evidence must match included chunk IDs in order")
        if self.assessment.context_chunk_ids != self.context.included_chunk_ids:
            raise ValueError("context assessment must match included chunk IDs")
        if self.assessment.omitted_chunk_ids != self.context.omitted_chunk_ids:
            raise ValueError("context assessment must match omitted chunk IDs")
        if not self.assessment.should_abstain:
            raise ValueError("evidence-only context inspection requires abstention")
        if (
            self.authorization.policy_version != self.assessment.policy_version
            or self.authorization.sufficiency is not self.assessment.sufficiency
            or self.authorization.reason_codes != self.assessment.reason_codes
        ):
            raise ValueError("context authorization must project its exact assessment")
        return self


class GetEvidenceChunkResult(EvidenceModel):
    """Versioned direct lookup result inside the authorized corpus."""

    schema_version: Literal["get-pymc-chunk-v1"] = "get-pymc-chunk-v1"
    service_version: Literal["pymc-evidence-inspection-v1"] = "pymc-evidence-inspection-v1"
    corpus: AuthorizedCorpusMetadata
    chunk: AuthorizedEvidenceChunk
    authorization: EvidenceAuthorization


class EvidenceServiceError(ValueError):
    """Base error for safe translation at presentation boundaries."""


class UnknownEvidenceChunkError(EvidenceServiceError):
    """Raised when an opaque ID is absent from the authorized corpus."""


@dataclass(frozen=True, slots=True)
class EvidenceInspectionService:
    """Search and inspect authorized evidence without invoking answer generation."""

    documents: tuple[Document, ...]
    chunks: tuple[Chunk, ...]
    corpus: AuthorizedCorpusMetadata
    retriever: Retriever
    context_builder: ContextBuilder
    abstention_policy: AbstentionPolicy

    def __post_init__(self) -> None:
        """Reject mixed, incomplete, or provenance-poor service composition."""
        _validate_authorized_records(self.documents, self.chunks, self.corpus)

    def search(self, request: SearchEvidenceRequest) -> SearchEvidenceResult:
        """Return ranked authorized chunks and an explicit no-generation decision."""
        query = self._build_query(request.query, top_k=request.top_k)
        retrieved = tuple(self.retriever.retrieve(query))
        results = tuple(self._render_retrieved(item) for item in retrieved)
        if results:
            sufficiency = EvidenceSufficiency.NOT_ASSESSED
            reasons = ("no_calibrated_criterion", "retrieval_only")
        else:
            sufficiency = EvidenceSufficiency.INSUFFICIENT
            reasons = ("no_retrieved_evidence", "retrieval_only")
        return SearchEvidenceResult(
            normalized_query=request.query,
            query_sha256=_hash_normalized_query(request.query),
            requested_top_k=request.top_k,
            corpus=self.corpus,
            chunk_ids=tuple(result.chunk_id for result in results),
            results=results,
            authorization=EvidenceAuthorization(
                policy_version=self.abstention_policy.name,
                sufficiency=sufficiency,
                reason_codes=tuple(sorted(reasons)),
            ),
        )

    def inspect_context(
        self,
        request: InspectEvidenceContextRequest,
    ) -> InspectEvidenceContextResult:
        """Build context, apply the real policy, and expose its abstention exactly."""
        query = self._build_query(request.query, top_k=CONTEXT_RETRIEVAL_TOP_K)
        retrieved = self.retriever.retrieve(query)
        context = self.context_builder.build(
            query,
            retrieved,
            token_budget=request.token_budget,
        )
        assessment = self.abstention_policy.assess(context)
        if not assessment.should_abstain:
            raise EvidenceServiceError(
                "evidence-only service refuses an answer-permitting policy result"
            )
        retrieved_by_id = {item.chunk.chunk_id: item for item in retrieved}
        evidence = tuple(
            self._render_retrieved(retrieved_by_id[chunk_id])
            for chunk_id in context.included_chunk_ids
        )
        return InspectEvidenceContextResult(
            normalized_query=request.query,
            query_sha256=_hash_normalized_query(request.query),
            corpus=self.corpus,
            context_sha256=canonical_json_sha256(context.model_dump(mode="json")),
            context=context,
            evidence=evidence,
            assessment=assessment,
            authorization=EvidenceAuthorization(
                policy_version=assessment.policy_version,
                sufficiency=assessment.sufficiency,
                reason_codes=assessment.reason_codes,
            ),
        )

    def get_chunk(self, request: GetEvidenceChunkRequest) -> GetEvidenceChunkResult:
        """Resolve one chunk by identity without accepting any path-like input."""
        chunk = next((item for item in self.chunks if item.chunk_id == request.chunk_id), None)
        if chunk is None:
            raise UnknownEvidenceChunkError("chunk ID is not present in the authorized PyMC corpus")
        return GetEvidenceChunkResult(
            corpus=self.corpus,
            chunk=self._render_chunk(chunk),
            authorization=EvidenceAuthorization(
                policy_version=self.abstention_policy.name,
                sufficiency=EvidenceSufficiency.NOT_ASSESSED,
                reason_codes=("chunk_lookup_only", "no_calibrated_criterion"),
            ),
        )

    @staticmethod
    def _build_query(text: str, *, top_k: int) -> SearchQuery:
        return SearchQuery(
            text=text,
            top_k=top_k,
            library="pymc",
            library_version="6.2.0",
            source_types=(SourceType.API_REFERENCE,),
        )

    def _render_retrieved(self, item: RetrievedChunk) -> AuthorizedEvidenceChunk:
        return self._render_chunk(item.chunk, rank=item.rank, score=item.score)

    def _render_chunk(
        self,
        chunk: Chunk,
        *,
        rank: int | None = None,
        score: float | None = None,
    ) -> AuthorizedEvidenceChunk:
        document = next(
            (item for item in self.documents if item.document_id == chunk.document_id),
            None,
        )
        if document is None:
            raise EvidenceServiceError("authorized chunk has no authorized parent document")
        if (
            document.source_commit is None
            or document.license_name is None
            or document.license_url is None
            or document.parser_version is None
            or chunk.chunker_version is None
        ):
            raise EvidenceServiceError("authorized evidence provenance is incomplete")
        return AuthorizedEvidenceChunk(
            chunk_id=chunk.chunk_id,
            rank=rank,
            score=score,
            title=chunk.title,
            section=chunk.section,
            api_symbols=chunk.api_symbols,
            library="pymc",
            library_version="6.2.0",
            source_type="api_reference",
            content_sha256=chunk.content_hash,
            text=chunk.content,
            provenance=EvidenceProvenance(
                document_id=document.document_id,
                document_content_sha256=document.content_hash,
                source_url=document.source_url,
                source_commit=document.source_commit,
                license_name=document.license_name,
                license_url=document.license_url,
                parser_version=document.parser_version,
                chunker_version=chunk.chunker_version,
            ),
        )


def _normalize_query(value: object) -> object:
    if not isinstance(value, str):
        return value
    if any(
        category(character) in {"Cc", "Cf", "Cs"} and not character.isspace() for character in value
    ):
        raise ValueError("query contains unsupported control characters")
    return " ".join(normalize("NFKC", value).split())


def _hash_normalized_query(query: str) -> str:
    return sha256(query.encode("utf-8")).hexdigest()


def _validate_authorized_records(
    documents: Sequence[Document],
    chunks: Sequence[Chunk],
    corpus: AuthorizedCorpusMetadata,
) -> None:
    if not documents or not chunks:
        raise EvidenceServiceError("authorized PyMC corpus must contain documents and chunks")
    if len(documents) != corpus.document_count or len(chunks) != corpus.chunk_count:
        raise EvidenceServiceError("authorized PyMC corpus counts do not match its metadata")
    document_ids = {item.document_id for item in documents}
    if len(document_ids) != len(documents):
        raise EvidenceServiceError("authorized PyMC corpus contains duplicate documents")
    chunk_ids = {item.chunk_id for item in chunks}
    if len(chunk_ids) != len(chunks):
        raise EvidenceServiceError("authorized PyMC corpus contains duplicate chunks")
    for document in documents:
        if (
            document.library != corpus.library
            or document.library_version != corpus.library_version
            or document.source_type is not SourceType.API_REFERENCE
            or document.source_commit != corpus.source_commit
            or document.license_name is None
            or document.license_url is None
            or document.parser_version is None
        ):
            raise EvidenceServiceError("authorized PyMC document provenance is incomplete")
    for chunk in chunks:
        if (
            chunk.document_id not in document_ids
            or chunk.library != corpus.library
            or chunk.library_version != corpus.library_version
            or chunk.source_type is not SourceType.API_REFERENCE
            or chunk.chunker_version is None
        ):
            raise EvidenceServiceError("authorized PyMC chunk crosses the corpus boundary")
