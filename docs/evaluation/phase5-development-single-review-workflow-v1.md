# Phase 5 development single-review workflow v1

## Purpose and authority boundary

This workflow records one genuine human review of the 24 agent-authored Phase 5 candidates under
`phase5-development-single-review-governance-v1`. It produces exploratory development evidence. It
does not produce independent adjudication, a held-out evaluation set, production-grade labels, or
an evidence-sufficiency threshold.

The four artifact classes remain distinct:

```text
agent candidate draft
        != pending review form
        != explicit single-human decision
        != independently adjudicated or held-out dataset
```

The reviewer uses the complete
[`phase5-development-batch-v1-review.md`](../../reports/evaluation/phase5-development-batch-v1-review.md)
packet. It includes all 15 frozen chunks so hard negatives are reviewed against the complete
admitted corpus. Retrieval ranks, context outcomes, policy scores, thresholds, generated answers,
and desired policy decisions remain outside the review boundary.

## Fixed identities and paths

| Field | Value |
|---|---|
| Dataset role | `development-single-review-exploratory` |
| Governance ID | `phase5-development-single-review-governance-v1` |
| Governance SHA-256 | `a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264` |
| Reviewer ID | `sr_001` |
| Candidate batch ID | `pymc-6.1.0-api-phase5-development-batch-v1` |
| Candidate SHA-256 | `832075827b782c26b4975635f19b836439a2a0d582e36fa59704ee19bbb15abb` |
| Corpus hash policy | `canonical-chunk-identity-json-v1` |
| Corpus SHA-256 | `af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2` |
| Human decision path | `datasets/evaluation/phase5/reviews/development-single-review-v1.decisions.jsonl` |
| Accepted-only dataset | `datasets/evaluation/phase5/development-single-review-v1.jsonl` |
| Validation report | `reports/evaluation/phase5-development-single-review-v1-validation.json` |

The governance document is immutable: its exact bytes must continue to hash to the value above.
Completion status belongs in this workflow and the validation report, not in a rewritten governance
record.

## Completion record

The governed review completed on 2026-08-02. All 24 candidates received explicit decisions from
`sr_001`; all were accepted as proposed. The resulting dataset contains 18 corpus-answerable
queries, six hard negatives, 28 atomic claims, and 31 minimal support sets. No independent
adjudication, held-out evaluation, or threshold selection occurred.

- Decision SHA-256: `3bb0aa56adb8fc664c65020ee64c54f5b1aecf30d918b24ceeec75323556da2e`
- Dataset SHA-256: `bf9c9b515fe0b886db88199b94a2b24f1a60ad60273bd7e266f6d0f757ceab15`

The commands below remain the reproducible procedure for rebuilding or independently checking the
artifacts. A pending template must never overwrite the completed decision file.

## Prepare the offline corpus and pending form

Build the exact frozen corpus from the four checked-in manifests and fixtures using the ingestion
commands in the README. Confirm that it contains four documents, 15 chunks, and corpus SHA-256
`af0b6d...`.

Then export the editable decision file:

```bash
uv run python -m tools.research_cli export-development-single-review-template \
  --candidates datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl \
  --output datasets/evaluation/phase5/reviews/development-single-review-v1.decisions.jsonl
```

Every generated line has `final_status="pending"`, all component reviews `pending`, no timestamp,
no notes, and no revised content. This is a form, not human ground truth. The finalizer rejects it.

## Record one explicit decision per candidate

Review candidates in query-ID order with the packet open. For every record set all of:

- `query_review`;
- `corpus_answerability_review`;
- `claims_review`;
- `support_sets_review`;
- `leakage_review` after semantic near-duplicate inspection;
- `hard_negative_review` after inspecting the complete frozen corpus;
- `final_status`; and
- `reviewed_at` to the real review instant in UTC, for example with a `Z` suffix.

Allowed terminal outcomes are:

| Final status | Required content |
|---|---|
| `accepted-as-proposed` | All four semantic component fields are `accepted`; leakage is `confirmed-distinct`; hard-negative review is `confirmed` or `not-applicable`; `revised_content` is null. |
| `accepted-with-revisions` | Every semantic component is `accepted` or `revised`, at least one is `revised`, and `revised_content` supplies the complete reviewed query, answerability, hard-negative category, claims, and minimal support sets. Actual differences must match the declared revised fields. |
| `rejected` | At least one explicit rejection or duplicate decision, concise `review_notes`, and no `revised_content`. |
| `unresolved` | At least one unresolved component, concise `review_notes`, and no `revised_content`. |

For an accepted hard negative, `corpus_answerable` is false, `gold_claims` is empty, and the
hard-negative category is explicit. For an accepted answerable example, every necessary atomic
claim has one or more minimal support sets. Do not retain both a support set and its strict
superset. Do not preserve the preregistered 18/6 target by overriding human judgment.

## Finalize and validate

After all 24 records contain real decisions, run:

```bash
uv run python -m tools.research_cli finalize-development-single-review \
  --candidates datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl \
  --decisions datasets/evaluation/phase5/reviews/development-single-review-v1.decisions.jsonl \
  --corpus-dir datasets/processed/phase5-annotation-api-v1 \
  --dataset-output datasets/evaluation/phase5/development-single-review-v1.jsonl \
  --report-output reports/evaluation/phase5-development-single-review-v1-validation.json
```

The command fails before writing either output if a record is pending; identities differ; a UTC
timestamp is absent; a declared revision disagrees with its content; a support chunk is missing or
cross-version; or any strict model invariant fails. Accepted and accepted-with-revisions records
enter the dataset. Rejected and unresolved records do not; their IDs and counts remain in the
report.

Revalidate exact persisted bytes independently:

```bash
uv run python -m tools.research_cli validate-development-single-review \
  --candidates datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl \
  --decisions datasets/evaluation/phase5/reviews/development-single-review-v1.decisions.jsonl \
  --dataset datasets/evaluation/phase5/development-single-review-v1.jsonl \
  --corpus-dir datasets/processed/phase5-annotation-api-v1
```

The emitted report records the SHA-256 of the exact decision and dataset bytes, candidate and
governance hashes, corpus identity, reviewer ID, outcome counts and IDs, accepted claim/support
counts, resolved chunk IDs, and the single-review limitations. It never asserts semantic
correctness from structural resolution.

## Next gate

The unchanged conservative-policy baseline is now recorded in
[`phase5-development-single-review-v1-conservative-baseline.json`](../../reports/evaluation/phase5-development-single-review-v1-conservative-baseline.json).
It authorized zero answers, as expected, and selected no threshold. Its retrieval/context coverage
is diagnostic rather than an answer-permitting rule.

The current next gate is a preregistered, PyMC-only official API expansion followed by new human
evaluation on the stabilized corpus. Do not reinterpret the PyMC 6.1.0 single-review decisions as
new 6.2.0 judgments, or select an answer-permitting signal, loss, or threshold before a prospective
calibration design and suitable development/held-out data are fixed.
