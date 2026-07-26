# Phase 5 development single-review governance v1

## Status and decision

- Status: **Accepted — explicit project-scope decision**
- Governance ID: `phase5-development-single-review-governance-v1`
- Decision reviewer ID: `mlioi`
- Decided at (UTC): `2026-07-26T04:14:51Z`
- Dataset role: `development-single-review-exploratory`
- Intended example reviewer ID: `sr_001`

The project owner is working alone and explicitly selected a one-human exploratory evaluation
boundary. This decision replaces the requirement for a second independent adjudicator for this
development batch. It does not represent one person as two reviewers and does not claim that an
independent adjudication occurred.

The earlier statement that `ann_001` and `adj_001` represented two available people was based on
a misunderstanding of those identifiers. That availability statement is withdrawn. Neither
identifier records completed example-level review, and no accepted or single-reviewed dataset
exists at the time of this decision.

## Relationship to the original preregistration

This governance record supersedes only the annotation/adjudication roles, accepted-dataset path,
and independent-review exit criteria in
`phase5-development-batch-preregistration-v1`. The following design choices remain fixed:

- the frozen PyMC 6.1.0 API-only corpus and its limitations;
- the 24 construction slots and the 18/6 answerability target;
- all difficulty, intent, query-family, template-family, API-symbol, claim-complexity, and
  near-boundary matrices;
- the hard-negative categories, leakage controls, blinding rules, and prohibition on tuning from
  runtime outcomes; and
- the semantic requirements for atomic claims and alternative minimal support sets.

The governance decision was made after agent-authored candidates were drafted but before any
human example labels were recorded and before retrieval, context, or evidence-policy outcomes
were run. It therefore changes the strength of review, not the candidate selection or labels.

## Bound artifacts

| Field | Fixed value |
|---|---|
| Original design preregistration | `phase5-development-batch-preregistration-v1` |
| Candidate batch | `pymc-6.1.0-api-phase5-development-batch-v1` |
| Candidate path | `datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl` |
| Candidate SHA-256 | `832075827b782c26b4975635f19b836439a2a0d582e36fa59704ee19bbb15abb` |
| Review packet | `reports/evaluation/phase5-development-batch-v1-review.md` |
| Future reviewed dataset | `datasets/evaluation/phase5/development-single-review-v1.jsonl` |
| Future validation report | `reports/evaluation/phase5-development-single-review-v1-validation.json` |
| Corpus hash policy | `canonical-chunk-identity-json-v1` |
| Corpus SHA-256 | `af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2` |

The candidate and packet paths are retained so the already prepared drafts remain
content-addressable. Only the future human-reviewed dataset and validation report use the
`single-review` name. The existing `Phase5DevelopmentExample` and
`load_phase5_development_dataset` contracts require independent adjudication and must not be used
to persist this single-review dataset. A separate strict single-review contract is required before
review decisions are converted into JSONL.

## One-human review procedure

The person represented by `sr_001` must inspect every candidate against the complete frozen
corpus appendix without looking at retrieval ranks, context outcomes, evidence-policy signals, or
desired downstream decisions. For every example, the reviewer must:

1. accept, revise, or reject the query as realistic and non-duplicative;
2. accept or revise the corpus-relative answerability judgment;
3. accept or revise every atomic claim, or confirm that a hard negative has no valid claim;
4. accept or revise every alternative minimal support set;
5. record a real UTC review timestamp and an explicit final decision; and
6. leave rejected or unresolved records outside the reviewed dataset.

The reviewer may perform a later self-check, but it remains the same human review and must not be
described as independent adjudication. The agent may prepare views, validate identities, and
persist the reviewer's explicit decisions, but agent proposals are not human labels.

## Claims that are and are not permitted

A completed `development-single-review-v1` dataset may be used for local exploratory engineering,
the conservative-policy baseline, error analysis, and provisional evidence-policy experiments. It
must carry the `development-single-review-exploratory` role and this governance identity in every
derived report.

It does not support claims that:

- labels or minimal support sets were independently adjudicated;
- measured selective risk is independently validated;
- a threshold is trustworthy for unsupervised, production, or high-stakes use;
- a future held-out result is independent merely because it uses different records; or
- structural chunk resolution establishes semantic correctness.

Any answer-permitting policy developed from this dataset remains provisional and suitable only for
the supervised local MVP boundary. Reports must separate measured counts from the human judgment
and explicitly name the single-review limitation. Adding a genuinely independent reviewer later
creates a new review identity, dataset hash, and affected downstream reports; it must not silently
upgrade this dataset's provenance.

## Exit criteria for this governance unit

This governance change is complete only when:

- the explicit one-human decision, reviewer ID, and UTC timestamp are recorded;
- the mistaken two-person availability statement is explicitly withdrawn without fabricating
  review history;
- the future dataset and report paths include `single-review`;
- candidates remain drafts and no human labels are inferred from this decision;
- the review packet describes one real human review and no independent adjudication;
- repository documentation distinguishes exploratory use from independent validation; and
- deterministic checks bind the packet to the unchanged candidate and corpus identities.

The next human action is the actual per-example review by `sr_001`. This governance decision alone
does not accept any candidate.
