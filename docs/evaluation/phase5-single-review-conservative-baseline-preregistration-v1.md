# Phase 5 single-review conservative baseline preregistration v1

## Status and purpose

- Status: fixed before baseline execution
- Recorded at: `2026-08-02T02:48:48Z`
- Dataset role: `development-single-review-exploratory`
- Evaluator: `phase5-single-review-gold-evidence-v1`

This engineering preregistration fixes the deterministic retrieval, context, and evidence-policy
configuration before observing the baseline outcomes. It is not a human annotation, independent
adjudication, held-out evaluation, or threshold-selection decision.

## Governed inputs

| Identity | Fixed value |
| --- | --- |
| Governance ID | `phase5-development-single-review-governance-v1` |
| Governance SHA-256 | `a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264` |
| Candidate batch ID | `pymc-6.1.0-api-phase5-development-batch-v1` |
| Candidate batch SHA-256 | `832075827b782c26b4975635f19b836439a2a0d582e36fa59704ee19bbb15abb` |
| Decisions SHA-256 | `3bb0aa56adb8fc664c65020ee64c54f5b1aecf30d918b24ceeec75323556da2e` |
| Dataset SHA-256 | `bf9c9b515fe0b886db88199b94a2b24f1a60ad60273bd7e266f6d0f757ceab15` |
| Corpus SHA-256 | `af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2` |

## Fixed runtime configuration

| Component | Fixed value |
| --- | --- |
| Retriever | `bm25-v1` |
| Tokenizer | `technical-v1` |
| BM25 parameters | `k1=1.5`; `b=0.75` |
| Candidate depth | `top_k=3` |
| Context builder | `ranked-context-v1` |
| Rendering | `context-item-text-v1` |
| Truncation | `rank-prefix-whole-item-v1` |
| Technical-token budget | `2048` |
| Evidence policy | `conservative-no-threshold-v1` |

Expected API symbols from the human-reviewed examples are not supplied as retrieval filters. Doing
so would leak gold routing metadata into the measured retrieval result. Queries are filtered only
to the reviewed `pymc` `6.1.0` API-reference boundary.

## Fixed measurements

The report records all 24 examples, candidate and admitted-context claim coverage, budget-only
support loss, answer coverage, selective risk, false-answer rate, false-abstention rate, and decision
accuracy. Undefined conditional rates remain `null`.

The conservative policy is expected to authorize zero answers. That expectation must not be used to
change labels, runtime parameters, or policy behavior after execution. The result selects no
evidence signal, loss, equality rule, or threshold.

## Reproduction command

```bash
uv run python -m tools.research_cli evaluate-development-single-review-baseline \
  --candidates datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl \
  --decisions datasets/evaluation/phase5/reviews/development-single-review-v1.decisions.jsonl \
  --dataset datasets/evaluation/phase5/development-single-review-v1.jsonl \
  --corpus-dir datasets/processed/phase5-annotation-api-v1 \
  --top-k 3 \
  --token-budget 2048 \
  --k1 1.5 \
  --b 0.75 \
  --report-output reports/evaluation/phase5-development-single-review-v1-conservative-baseline.json
```
