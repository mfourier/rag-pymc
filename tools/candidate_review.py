"""Strict Phase 5 candidate loading and deterministic human review export."""

import json
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rag_pymc.domain import Chunk, Difficulty
from rag_pymc.evaluation.development_models import (
    Phase5DevelopmentCandidate,
    Phase5DevelopmentCandidateBatch,
)
from rag_pymc.evaluation.errors import EvaluationDatasetError
from tools.development_dataset import hash_phase5_corpus

PREREGISTRATION_ID = "phase5-development-batch-preregistration-v1"
BATCH_ID = "pymc-6.1.0-api-phase5-development-batch-v1"
REVIEW_GOVERNANCE_ID = "phase5-development-single-review-governance-v1"
REVIEW_GOVERNANCE_SHA256 = "a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264"
SINGLE_REVIEWER_ID = "sr_001"
NORMALIZATION_POLICY = "nfkc-casefold-whitespace-v1"


@dataclass(frozen=True)
class _SlotSpec:
    """One code-checked projection of the approved Gate B slot registry."""

    query_id: str
    answerable: bool
    query_family: str
    template_family: str
    intent: str
    difficulty: Difficulty
    expected_api_symbols: tuple[str, ...]
    claim_count: int
    hard_negative_category: str | None = None


@dataclass(frozen=True)
class PriorQuery:
    """Minimal historical query identity used for leakage triage."""

    question_id: str
    question: str


@dataclass(frozen=True)
class PriorQuerySource:
    """One prior query collection used only for deterministic leakage triage."""

    path: str
    dataset_sha256: str
    queries: tuple[PriorQuery, ...]


def _slot(
    number: int,
    *,
    answerable: bool,
    query_family: str,
    template_family: str,
    intent: str,
    difficulty: Difficulty,
    symbols: tuple[str, ...],
    claim_count: int,
    hard_negative_category: str | None = None,
) -> tuple[str, _SlotSpec]:
    suffix = f"{number:03d}"
    return (
        f"p5dev_v1_slot_{suffix}",
        _SlotSpec(
            query_id=f"p5dev_v1_query_{suffix}",
            answerable=answerable,
            query_family=query_family,
            template_family=template_family,
            intent=intent,
            difficulty=difficulty,
            expected_api_symbols=tuple(sorted(symbols)),
            claim_count=claim_count,
            hard_negative_category=hard_negative_category,
        ),
    )


_OPERATION_NEGATIVE = "nearby-api-does-not-support-requested-operation"
_GUARANTEE_NEGATIVE = "documented-options-do-not-establish-requested-guarantee"
_BATCH_V1_SLOTS = dict(
    (
        _slot(
            1,
            answerable=True,
            query_family="sampling_controls",
            template_family="direct_function_contract",
            intent="api_usage",
            difficulty=Difficulty.BEGINNER,
            symbols=("pymc.sample",),
            claim_count=1,
        ),
        _slot(
            2,
            answerable=True,
            query_family="sampling_controls",
            template_family="parameter_behavior",
            intent="parameter_behavior",
            difficulty=Difficulty.BEGINNER,
            symbols=("pymc.sample",),
            claim_count=1,
        ),
        _slot(
            3,
            answerable=True,
            query_family="sampling_controls",
            template_family="input_constraint",
            intent="parameter_behavior",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.sample",),
            claim_count=2,
        ),
        _slot(
            4,
            answerable=True,
            query_family="sampling_output_contract",
            template_family="output_contract",
            intent="return_and_storage",
            difficulty=Difficulty.BEGINNER,
            symbols=("pymc.sample",),
            claim_count=1,
        ),
        _slot(
            5,
            answerable=True,
            query_family="sampling_output_contract",
            template_family="input_constraint",
            intent="version_sensitive",
            difficulty=Difficulty.ADVANCED,
            symbols=("pymc.sample",),
            claim_count=3,
        ),
        _slot(
            6,
            answerable=True,
            query_family="data_container_contract",
            template_family="direct_function_contract",
            intent="api_usage",
            difficulty=Difficulty.BEGINNER,
            symbols=("pymc.Data",),
            claim_count=1,
        ),
        _slot(
            7,
            answerable=True,
            query_family="data_container_contract",
            template_family="parameter_behavior",
            intent="parameter_behavior",
            difficulty=Difficulty.BEGINNER,
            symbols=("pymc.Data",),
            claim_count=1,
        ),
        _slot(
            8,
            answerable=True,
            query_family="data_container_contract",
            template_family="procedural_workflow",
            intent="api_usage",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.Data",),
            claim_count=2,
        ),
        _slot(
            9,
            answerable=True,
            query_family="data_update_contract",
            template_family="direct_function_contract",
            intent="api_usage",
            difficulty=Difficulty.BEGINNER,
            symbols=("pymc.model.core.set_data",),
            claim_count=1,
        ),
        _slot(
            10,
            answerable=True,
            query_family="data_update_contract",
            template_family="parameter_behavior",
            intent="parameter_behavior",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.model.core.set_data",),
            claim_count=1,
        ),
        _slot(
            11,
            answerable=True,
            query_family="data_update_contract",
            template_family="procedural_workflow",
            intent="api_usage",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.model.core.set_data",),
            claim_count=2,
        ),
        _slot(
            12,
            answerable=True,
            query_family="posterior_predictive_controls",
            template_family="direct_function_contract",
            intent="api_usage",
            difficulty=Difficulty.BEGINNER,
            symbols=("pymc.sample_posterior_predictive",),
            claim_count=1,
        ),
        _slot(
            13,
            answerable=True,
            query_family="posterior_predictive_controls",
            template_family="parameter_behavior",
            intent="parameter_behavior",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.sample_posterior_predictive",),
            claim_count=1,
        ),
        _slot(
            14,
            answerable=True,
            query_family="posterior_predictive_output_contract",
            template_family="output_contract",
            intent="return_and_storage",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.sample_posterior_predictive",),
            claim_count=1,
        ),
        _slot(
            15,
            answerable=True,
            query_family="posterior_predictive_controls",
            template_family="output_contract",
            intent="return_and_storage",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.sample_posterior_predictive",),
            claim_count=2,
        ),
        _slot(
            16,
            answerable=True,
            query_family="mutable_prediction_workflow",
            template_family="procedural_workflow",
            intent="workflow_composition",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.Data", "pymc.model.core.set_data"),
            claim_count=2,
        ),
        _slot(
            17,
            answerable=True,
            query_family="mutable_prediction_workflow",
            template_family="input_constraint",
            intent="workflow_composition",
            difficulty=Difficulty.ADVANCED,
            symbols=("pymc.Data", "pymc.model.core.set_data"),
            claim_count=2,
        ),
        _slot(
            18,
            answerable=True,
            query_family="mutable_prediction_workflow",
            template_family="procedural_workflow",
            intent="workflow_composition",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.model.core.set_data", "pymc.sample_posterior_predictive"),
            claim_count=3,
        ),
        _slot(
            19,
            answerable=False,
            query_family="sampling_controls",
            template_family="unsupported_guarantee_contrast",
            intent="version_sensitive",
            difficulty=Difficulty.ADVANCED,
            symbols=("pymc.sample",),
            claim_count=0,
            hard_negative_category=_GUARANTEE_NEGATIVE,
        ),
        _slot(
            20,
            answerable=False,
            query_family="sampling_output_contract",
            template_family="unsupported_operation_contrast",
            intent="return_and_storage",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.sample",),
            claim_count=0,
            hard_negative_category=_OPERATION_NEGATIVE,
        ),
        _slot(
            21,
            answerable=False,
            query_family="data_container_contract",
            template_family="unsupported_guarantee_contrast",
            intent="version_sensitive",
            difficulty=Difficulty.ADVANCED,
            symbols=("pymc.Data",),
            claim_count=0,
            hard_negative_category=_GUARANTEE_NEGATIVE,
        ),
        _slot(
            22,
            answerable=False,
            query_family="data_update_contract",
            template_family="unsupported_operation_contrast",
            intent="api_usage",
            difficulty=Difficulty.BEGINNER,
            symbols=("pymc.model.core.set_data",),
            claim_count=0,
            hard_negative_category=_OPERATION_NEGATIVE,
        ),
        _slot(
            23,
            answerable=False,
            query_family="posterior_predictive_controls",
            template_family="unsupported_guarantee_contrast",
            intent="parameter_behavior",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.sample_posterior_predictive",),
            claim_count=0,
            hard_negative_category=_GUARANTEE_NEGATIVE,
        ),
        _slot(
            24,
            answerable=False,
            query_family="mutable_prediction_workflow",
            template_family="unsupported_operation_contrast",
            intent="workflow_composition",
            difficulty=Difficulty.INTERMEDIATE,
            symbols=("pymc.Data", "pymc.sample_posterior_predictive"),
            claim_count=0,
            hard_negative_category=_OPERATION_NEGATIVE,
        ),
    )
)


def load_phase5_development_candidates(path: Path) -> Phase5DevelopmentCandidateBatch:
    """Load strict agent-draft JSONL without manufacturing human provenance."""
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        msg = f"unable to read Phase 5 development candidates: {path}"
        raise EvaluationDatasetError(msg) from error

    try:
        text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        line_number = raw_bytes[: error.start].count(b"\n") + 1
        msg = f"invalid UTF-8 in Phase 5 development candidates at {path}:{line_number}"
        raise EvaluationDatasetError(msg) from error

    candidates: list[Phase5DevelopmentCandidate] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(
                line,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_non_finite_json_number,
            )
            candidates.append(Phase5DevelopmentCandidate.model_validate(payload))
        except (json.JSONDecodeError, RecursionError, ValidationError, ValueError) as error:
            msg = f"invalid Phase 5 development candidate at {path}:{line_number}"
            raise EvaluationDatasetError(msg) from error

    if not candidates:
        msg = f"Phase 5 development candidate file is empty: {path}"
        raise EvaluationDatasetError(msg)

    first = candidates[0]
    try:
        return Phase5DevelopmentCandidateBatch(
            dataset_sha256=sha256(raw_bytes).hexdigest(),
            preregistration_id=first.preregistration_id,
            batch_id=first.batch_id,
            corpus_hash_policy=first.corpus_hash_policy,
            corpus_sha256=first.corpus_sha256,
            candidates=tuple(candidates),
        )
    except ValidationError as error:
        msg = f"invalid Phase 5 development candidate batch: {path}"
        raise EvaluationDatasetError(msg) from error


def validate_phase5_candidate_batch_v1(batch: Phase5DevelopmentCandidateBatch) -> None:
    """Require exact agreement with every slot in the human-approved Gate B design."""
    batch = Phase5DevelopmentCandidateBatch.model_validate(batch)
    by_slot = {candidate.slot_id: candidate for candidate in batch.candidates}
    if set(by_slot) != set(_BATCH_V1_SLOTS):
        missing = tuple(sorted(set(_BATCH_V1_SLOTS) - set(by_slot)))
        unexpected = tuple(sorted(set(by_slot) - set(_BATCH_V1_SLOTS)))
        msg = (
            "Phase 5 candidate slots differ from Gate B; "
            f"missing={missing}, unexpected={unexpected}"
        )
        raise EvaluationDatasetError(msg)

    for slot_id, spec in sorted(_BATCH_V1_SLOTS.items()):
        candidate = by_slot[slot_id]
        observed = (
            candidate.query_id,
            candidate.proposed_corpus_answerable,
            candidate.query_family,
            candidate.template_family,
            candidate.intent,
            candidate.difficulty,
            candidate.expected_api_symbols,
            len(candidate.proposed_gold_claims),
            candidate.hard_negative_category,
        )
        expected = (
            spec.query_id,
            spec.answerable,
            spec.query_family,
            spec.template_family,
            spec.intent,
            spec.difficulty,
            spec.expected_api_symbols,
            spec.claim_count,
            spec.hard_negative_category,
        )
        if observed != expected:
            msg = f"Phase 5 candidate {slot_id} differs from its approved Gate B slot"
            raise EvaluationDatasetError(msg)


def validate_phase5_candidate_corpus(
    batch: Phase5DevelopmentCandidateBatch,
    chunks: Sequence[Chunk],
) -> tuple[Chunk, ...]:
    """Resolve every proposed support set against the exact frozen corpus."""
    batch = Phase5DevelopmentCandidateBatch.model_validate(batch)
    validated_chunks = tuple(Chunk.model_validate(chunk) for chunk in chunks)
    actual_hash = hash_phase5_corpus(validated_chunks)
    if actual_hash != batch.corpus_sha256:
        msg = (
            "Phase 5 candidate corpus SHA-256 mismatch: "
            f"expected {batch.corpus_sha256}, got {actual_hash}"
        )
        raise EvaluationDatasetError(msg)

    chunks_by_id = {chunk.chunk_id: chunk for chunk in validated_chunks}
    for candidate in batch.candidates:
        for claim in candidate.proposed_gold_claims:
            for support_set in claim.support_sets:
                for chunk_id in support_set.chunk_ids:
                    chunk = chunks_by_id.get(chunk_id)
                    if chunk is None:
                        msg = (
                            f"Phase 5 candidate claim {claim.claim_id} references missing "
                            f"{chunk_id}"
                        )
                        raise EvaluationDatasetError(msg)
                    if (
                        chunk.library.casefold() != candidate.library.casefold()
                        or chunk.library_version != candidate.library_version
                    ):
                        msg = (
                            f"Phase 5 candidate claim {claim.claim_id} references {chunk_id} "
                            "from a different library or version"
                        )
                        raise EvaluationDatasetError(msg)
    return tuple(sorted(validated_chunks, key=lambda chunk: chunk.chunk_id))


def load_prior_query_source(path: Path) -> PriorQuerySource:
    """Load prior question text without exposing qrels or experiment outcomes in the packet."""
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        msg = f"unable to read prior evaluation queries: {path}"
        raise EvaluationDatasetError(msg) from error
    return PriorQuerySource(
        path=path.as_posix(),
        dataset_sha256=sha256(raw_bytes).hexdigest(),
        queries=_load_prior_queries(raw_bytes, path),
    )


def _load_prior_queries(raw_bytes: bytes, path: Path) -> tuple[PriorQuery, ...]:
    try:
        text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        msg = f"invalid UTF-8 in prior evaluation queries: {path}"
        raise EvaluationDatasetError(msg) from error

    queries: list[PriorQuery] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(
                line,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_non_finite_json_number,
            )
            question_id = payload["question_id"]
            question = payload["question"]
            if not isinstance(question_id, str) or not question_id.strip():
                raise ValueError
            if not isinstance(question, str) or not question.strip():
                raise ValueError
            queries.append(PriorQuery(question_id=question_id.strip(), question=question.strip()))
        except (KeyError, TypeError, json.JSONDecodeError, RecursionError, ValueError) as error:
            msg = f"invalid prior evaluation query at {path}:{line_number}"
            raise EvaluationDatasetError(msg) from error
    if not queries:
        msg = f"prior evaluation query file is empty: {path}"
        raise EvaluationDatasetError(msg)
    return tuple(queries)


def render_phase5_candidate_review(
    batch: Phase5DevelopmentCandidateBatch,
    chunks: Sequence[Chunk],
    prior_sources: Sequence[PriorQuerySource],
) -> str:
    """Render a deterministic review packet containing proposals and resolved evidence."""
    batch = Phase5DevelopmentCandidateBatch.model_validate(batch)
    validated_chunks = validate_phase5_candidate_corpus(batch, chunks)
    sources = tuple(sorted(prior_sources, key=lambda source: source.path))
    leakage_matches = _build_leakage_matches(batch.candidates, sources)

    answerable_count = sum(candidate.proposed_corpus_answerable for candidate in batch.candidates)
    claim_count = sum(len(candidate.proposed_gold_claims) for candidate in batch.candidates)
    support_set_count = sum(
        len(claim.support_sets)
        for candidate in batch.candidates
        for claim in candidate.proposed_gold_claims
    )
    referenced_ids = {
        chunk_id
        for candidate in batch.candidates
        for claim in candidate.proposed_gold_claims
        for support_set in claim.support_sets
        for chunk_id in support_set.chunk_ids
    }

    lines = [
        "# Phase 5 development batch v1 single-review candidate packet",
        "",
        "> Status: Agent-authored draft awaiting one real human review. No human review is "
        "recorded.",
        "",
        "## Fixed identities",
        "",
        f"- Design preregistration: `{batch.preregistration_id}`",
        f"- Review governance: `{REVIEW_GOVERNANCE_ID}`",
        f"- Review-governance SHA-256: `{REVIEW_GOVERNANCE_SHA256}`",
        f"- Intended single reviewer: `{SINGLE_REVIEWER_ID}` (review not yet performed)",
        f"- Batch: `{batch.batch_id}`",
        f"- Candidate SHA-256: `{batch.dataset_sha256}`",
        f"- Corpus hash policy: `{batch.corpus_hash_policy}`",
        f"- Corpus SHA-256: `{batch.corpus_sha256}`",
        f"- Candidate count: {len(batch.candidates)}",
        f"- Proposed answerable count: {answerable_count}",
        f"- Proposed hard-negative count: {len(batch.candidates) - answerable_count}",
        f"- Proposed claim count: {claim_count}",
        f"- Proposed support-set count: {support_set_count}",
        f"- Referenced chunk count: {len(referenced_ids)}",
        "",
        "## Leakage triage boundary",
        "",
        f"- Normalization policy: `{NORMALIZATION_POLICY}`",
        "- Exact normalized duplicates are rejected before this packet is rendered.",
        "- Lexical overlap is triage only; it is not retrieval evidence or a leakage decision.",
        "- Every candidate still requires human semantic near-duplicate review.",
    ]
    for source in sources:
        lines.append(f"- Prior questions: `{source.path}` (`{source.dataset_sha256}`)")
    lines.extend(
        [
            "",
            "## Candidate decisions",
            "",
            "For every candidate, the single human reviewer must accept, revise, or reject the "
            "query, corpus-relative label, claims, and minimal support sets. This review is not "
            "independent adjudication.",
            "",
        ]
    )

    for candidate in sorted(batch.candidates, key=lambda item: item.query_id):
        lines.extend(_render_candidate(candidate, leakage_matches[candidate.query_id]))

    lines.extend(
        [
            "## Frozen corpus appendix",
            "",
            "The appendix contains all 15 chunks so hard negatives can be reviewed against the "
            "complete admitted corpus, not only nearby evidence selected by the agent.",
            "",
        ]
    )
    for chunk in validated_chunks:
        lines.extend(_render_chunk(chunk))
    return "\n".join(lines).rstrip() + "\n"


def write_phase5_candidate_review(review: str, path: Path) -> None:
    """Write one deterministic Markdown packet after all validation succeeds."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(review, encoding="utf-8")
    except OSError as error:
        msg = f"unable to write Phase 5 candidate review packet: {path}"
        raise EvaluationDatasetError(msg) from error


def _render_candidate(
    candidate: Phase5DevelopmentCandidate,
    matches: tuple[tuple[float, PriorQuerySource, PriorQuery], ...],
) -> list[str]:
    lines = [
        f"### {candidate.query_id}",
        "",
        f"- Slot: `{candidate.slot_id}`",
        f"- Proposed corpus answerability: `{str(candidate.proposed_corpus_answerable).lower()}`",
        f"- Query family: `{candidate.query_family}`",
        f"- Template family: `{candidate.template_family}`",
        f"- Intent: `{candidate.intent}`",
        f"- Difficulty: `{candidate.difficulty.value}`",
        "- Expected API symbols: "
        + ", ".join(f"`{symbol}`" for symbol in candidate.expected_api_symbols),
        f"- Hard-negative category: `{candidate.hard_negative_category}`"
        if candidate.hard_negative_category
        else "- Hard-negative category: none",
        "",
        "#### Proposed query",
        "",
        f"> {candidate.query_text}",
        "",
        "#### Proposed claims and support",
        "",
    ]
    if not candidate.proposed_gold_claims:
        lines.extend(
            [
                "No claims or support sets are proposed. Review against the complete corpus "
                "appendix.",
                "",
            ]
        )
    for claim in candidate.proposed_gold_claims:
        lines.extend([f"- `{claim.claim_id}`: {claim.text}"])
        for index, support_set in enumerate(claim.support_sets, start=1):
            chunk_ids = ", ".join(f"`{chunk_id}`" for chunk_id in support_set.chunk_ids)
            lines.append(f"  - Alternative minimal set {index}: {chunk_ids}")
        lines.append("")

    lines.extend(["#### Prior-query lexical triage", ""])
    if not matches:
        lines.extend(["No prior query sources were supplied.", ""])
    else:
        for score, source, query in matches:
            lines.append(
                f"- Jaccard `{score:.6f}` — `{source.path}` / `{query.question_id}`: "
                f"{query.question}"
            )
        lines.append("")
    lines.extend(
        [
            "#### Single-human review checklist",
            "",
            "- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior "
            "evaluation data.",
            "- [ ] Proposed corpus-relative answerability is correct.",
            "- [ ] Every necessary proposition is an atomic claim, or no claim is valid for "
            "this hard negative.",
            "- [ ] Every support set is sufficient and minimal; all valid alternatives are "
            "represented.",
            "- [ ] Decision: accept / revise / reject (circle one in the review workflow).",
            "",
        ]
    )
    return lines


def _render_chunk(chunk: Chunk) -> list[str]:
    symbols = ", ".join(f"`{symbol}`" for symbol in chunk.api_symbols)
    lines = [
        f"### Evidence `{chunk.chunk_id}`",
        "",
        f"- Document: `{chunk.document_id}`",
        f"- Content SHA-256: `{chunk.content_hash}`",
        f"- Source: {chunk.source_url}",
        f"- Library: `{chunk.library}` `{chunk.library_version}`",
        f"- Source type: `{chunk.source_type.value}`",
        f"- Section: `{chunk.section}`",
        f"- API symbols: {symbols}",
        "",
    ]
    lines.extend(f"    {line}" if line else "" for line in chunk.content.splitlines())
    lines.append("")
    return lines


def _build_leakage_matches(
    candidates: Sequence[Phase5DevelopmentCandidate],
    sources: Sequence[PriorQuerySource],
) -> dict[str, tuple[tuple[float, PriorQuerySource, PriorQuery], ...]]:
    prior = tuple((source, query) for source in sources for query in source.queries)
    normalized_prior: dict[str, list[tuple[PriorQuerySource, PriorQuery]]] = {}
    for source, query in prior:
        normalized_prior.setdefault(_normalize_query(query.question), []).append((source, query))

    result: dict[str, tuple[tuple[float, PriorQuerySource, PriorQuery], ...]] = {}
    for candidate in candidates:
        normalized = _normalize_query(candidate.query_text)
        exact = normalized_prior.get(normalized, [])
        if exact:
            matches = tuple(f"{source.path}:{query.question_id}" for source, query in exact)
            msg = (
                f"Phase 5 candidate {candidate.query_id} exactly duplicates prior queries {matches}"
            )
            raise EvaluationDatasetError(msg)

        candidate_tokens = _query_tokens(normalized)
        scored = tuple(
            (
                _jaccard(candidate_tokens, _query_tokens(_normalize_query(query.question))),
                source,
                query,
            )
            for source, query in prior
        )
        result[candidate.query_id] = tuple(
            sorted(
                scored,
                key=lambda item: (-item[0], item[1].path, item[2].question_id),
            )[:3]
        )
    return result


def _normalize_query(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())


def _query_tokens(normalized: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z0-9_]+", normalized))


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_non_finite_json_number(_: str) -> None:
    raise ValueError("non-finite JSON number")
