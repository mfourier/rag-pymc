from dataclasses import fields
from hashlib import sha256

import pytest
from pydantic import ValidationError

from rag_pymc.application.evidence import (
    MAX_EVIDENCE_QUERY_CHARACTERS,
    MAX_EVIDENCE_TOKEN_BUDGET,
    MAX_EVIDENCE_TOP_K,
    AuthorizedCorpusMetadata,
    Bm25Parameters,
    EvidenceInspectionService,
    EvidenceProvenance,
    EvidenceServiceError,
    GetEvidenceChunkRequest,
    InspectEvidenceContextRequest,
    SearchEvidenceRequest,
)
from rag_pymc.application.retrieval_runtime import build_sparse_runtime
from rag_pymc.context import RankedContextBuilder
from rag_pymc.domain import (
    ConstructedContext,
    EvidenceAssessment,
    EvidenceSufficiency,
)
from tests.factories import make_chunk, make_document


def make_service(*, sufficient_policy: bool = False) -> EvidenceInspectionService:
    document = make_document(
        "doc_authorized",
        "Authorized PyMC API document.",
        library_version="6.2.0",
        source_url="https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html",
        source_commit="3b661c7e5e3ca7d5d7550eca36991d7c1e72274e",
        license_name="Apache-2.0",
        license_url="https://github.com/pymc-devs/pymc/blob/v6.2.0/LICENSE",
    )
    chunks = (
        make_chunk(
            "chunk_aaaaaaaaaaaaaaaaaaaa",
            "pymc.sample draws posterior samples and configures chains.",
            document=document,
            chunker_version="api-reference-v1",
        ),
        make_chunk(
            "chunk_bbbbbbbbbbbbbbbbbbbb",
            "pymc.Data creates a mutable data container.",
            document=document,
            chunker_version="api-reference-v1",
        ),
    )
    runtime = build_sparse_runtime(chunks)
    policy = SufficientPolicy() if sufficient_policy else ConservativePolicy()
    return EvidenceInspectionService(
        documents=(document,),
        chunks=chunks,
        corpus=AuthorizedCorpusMetadata(
            corpus_id="test-pymc-6.2.0",
            corpus_hash_policy="canonical-corpus-provenance-json-v2",
            corpus_sha256="a" * 64,
            legacy_content_hash_policy="canonical-chunk-identity-json-v1",
            legacy_content_sha256="b" * 64,
            library="pymc",
            library_version="6.2.0",
            release_tag="v6.2.0",
            source_commit="3b661c7e5e3ca7d5d7550eca36991d7c1e72274e",
            document_count=1,
            chunk_count=2,
            retriever="bm25-v1",
            tokenizer="technical-v1",
            bm25=Bm25Parameters(k1=1.5, b=0.75),
            limitations=("Test corpus is intentionally small.",),
        ),
        retriever=runtime.retriever,
        context_builder=RankedContextBuilder(runtime.tokenizer),
        abstention_policy=policy,
    )


class ConservativePolicy:
    name = "conservative-no-threshold-v1"

    def assess(self, context: ConstructedContext) -> EvidenceAssessment:
        included = context.included_chunk_ids
        if included:
            sufficiency = EvidenceSufficiency.NOT_ASSESSED
            reasons = ("no_calibrated_criterion",)
        else:
            sufficiency = EvidenceSufficiency.INSUFFICIENT
            reasons = ("no_retrieved_evidence",)
        return EvidenceAssessment(
            policy_version=self.name,
            sufficiency=sufficiency,
            should_abstain=True,
            reason_codes=reasons,
            context_chunk_ids=included,
            omitted_chunk_ids=context.omitted_chunk_ids,
        )


class SufficientPolicy:
    name = "unsafe-test-policy-v1"

    def assess(self, context: ConstructedContext) -> EvidenceAssessment:
        return EvidenceAssessment(
            policy_version=self.name,
            sufficiency=EvidenceSufficiency.SUFFICIENT,
            should_abstain=False,
            reason_codes=("synthetic_sufficiency",),
            context_chunk_ids=context.included_chunk_ids,
            omitted_chunk_ids=context.omitted_chunk_ids,
        )


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (SearchEvidenceRequest, {"query": " ", "version": "6.2.0", "top_k": 1}),
        (
            SearchEvidenceRequest,
            {"query": "x" * (MAX_EVIDENCE_QUERY_CHARACTERS + 1), "version": "6.2.0", "top_k": 1},
        ),
        (SearchEvidenceRequest, {"query": "query", "version": "6.1.0", "top_k": 1}),
        (SearchEvidenceRequest, {"query": "query", "version": "6.2.0", "top_k": 0}),
        (
            SearchEvidenceRequest,
            {"query": "query", "version": "6.2.0", "top_k": MAX_EVIDENCE_TOP_K + 1},
        ),
        (SearchEvidenceRequest, {"query": "query", "version": "6.2.0", "top_k": True}),
        (
            SearchEvidenceRequest,
            {"query": "visible\u202ehidden", "version": "6.2.0", "top_k": 1},
        ),
        (
            InspectEvidenceContextRequest,
            {"query": "query", "version": "6.2.0", "token_budget": 0},
        ),
        (
            InspectEvidenceContextRequest,
            {
                "query": "query",
                "version": "6.2.0",
                "token_budget": MAX_EVIDENCE_TOKEN_BUDGET + 1,
            },
        ),
        (
            GetEvidenceChunkRequest,
            {"chunk_id": "../../etc/passwd", "version": "6.2.0"},
        ),
    ],
)
def test_evidence_requests_reject_invalid_or_unbounded_inputs(
    model: type[SearchEvidenceRequest | InspectEvidenceContextRequest | GetEvidenceChunkRequest],
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_evidence_requests_normalize_unicode_and_whitespace_before_hashing() -> None:
    request = SearchEvidenceRequest(
        query="  What\t does\n pymc.\uff53\uff41\uff4d\uff50\uff4c\uff45 do?  ",
        version="6.2.0",
        top_k=2,
    )

    result = make_service().search(request)

    assert request.query == "What does pymc.sample do?"
    assert result.normalized_query == request.query
    assert result.query_sha256 == sha256(request.query.encode()).hexdigest()


def test_evidence_provenance_rejects_nonofficial_source_urls() -> None:
    with pytest.raises(ValidationError, match="official HTTPS PyMC documentation"):
        EvidenceProvenance.model_validate(
            {
                "document_id": "doc_untrusted",
                "document_content_sha256": "a" * 64,
                "source_url": "https://example.com/pymc.sample.html",
                "source_commit": "3b661c7e5e3ca7d5d7550eca36991d7c1e72274e",
                "license_name": "Apache-2.0",
                "license_url": "https://github.com/pymc-devs/pymc/blob/v6.2.0/LICENSE",
                "parser_version": "sphinx-api-v1",
                "chunker_version": "api-reference-v1",
            }
        )


def test_search_is_deterministic_ordered_and_fail_closed() -> None:
    service = make_service()
    request = SearchEvidenceRequest(query="posterior draws", version="6.2.0", top_k=2)

    first = service.search(request)
    second = service.search(request)

    assert first.model_dump_json() == second.model_dump_json()
    assert first.chunk_ids == ("chunk_aaaaaaaaaaaaaaaaaaaa",)
    assert tuple(item.rank for item in first.results) == (1,)
    assert first.results[0].text.startswith("pymc.sample")
    assert str(first.results[0].provenance.source_url).startswith("https://www.pymc.io/")
    assert first.corpus.retriever == "bm25-v1"
    assert first.corpus.tokenizer == "technical-v1"
    assert first.corpus.bm25 == Bm25Parameters(k1=1.5, b=0.75)
    assert first.authorization.should_abstain is True
    assert first.authorization.generation_permitted is False
    assert first.authorization.sufficiency is EvidenceSufficiency.NOT_ASSESSED


def test_context_exposes_exact_hash_provenance_and_conservative_assessment() -> None:
    result = make_service().inspect_context(
        InspectEvidenceContextRequest(
            query="posterior draws",
            version="6.2.0",
            token_budget=MAX_EVIDENCE_TOKEN_BUDGET,
        )
    )

    assert result.context.included_chunk_ids == ("chunk_aaaaaaaaaaaaaaaaaaaa",)
    assert tuple(item.chunk_id for item in result.evidence) == result.context.included_chunk_ids
    assert result.assessment.policy_version == "conservative-no-threshold-v1"
    assert result.assessment.should_abstain is True
    assert result.authorization.generation_permitted is False
    assert len(result.context_sha256) == 64
    assert (
        result.model_dump_json()
        == result.model_validate_json(result.model_dump_json()).model_dump_json()
    )


def test_direct_chunk_lookup_cannot_escape_the_authorized_identity_set() -> None:
    service = make_service()
    result = service.get_chunk(
        GetEvidenceChunkRequest(chunk_id="chunk_bbbbbbbbbbbbbbbbbbbb", version="6.2.0")
    )

    assert result.chunk.rank is None
    assert result.chunk.score is None
    assert result.chunk.text == "pymc.Data creates a mutable data container."
    assert result.authorization.reason_codes == (
        "chunk_lookup_only",
        "no_calibrated_criterion",
    )


def test_evidence_service_has_no_generator_and_refuses_positive_policy_results() -> None:
    assert "generator" not in {field.name for field in fields(EvidenceInspectionService)}
    service = make_service(sufficient_policy=True)

    with pytest.raises(EvidenceServiceError, match="refuses an answer-permitting policy"):
        service.inspect_context(
            InspectEvidenceContextRequest(
                query="posterior draws",
                version="6.2.0",
                token_budget=MAX_EVIDENCE_TOKEN_BUDGET,
            )
        )
