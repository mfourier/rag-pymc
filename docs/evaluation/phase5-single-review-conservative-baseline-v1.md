# Phase 5 single-review conservative baseline v1

## Result

The unchanged `conservative-no-threshold-v1` policy authorized no answers over the 24-example
single-human exploratory development dataset. This is the expected fail-closed baseline, not a
quality target and not evidence for an answer-permitting threshold.

The result is bound to the exact decisions, accepted-only dataset, agent candidate batch,
governance document, PyMC 6.1.0 annotation corpus, BM25 configuration, context builder, and
evidence policy. The preregistered configuration is recorded in
[`phase5-single-review-conservative-baseline-preregistration-v1.md`](phase5-single-review-conservative-baseline-preregistration-v1.md).

## Metrics

| Measurement | Result |
| --- | ---: |
| Reviewed queries | 24 |
| Corpus-answerable / hard negatives | 18 / 6 |
| Gold claims | 28 |
| Claims covered by top-3 candidates | 26 / 28 (`0.928571`) |
| Claims admitted to 2048-unit context | 25 / 28 (`0.892857`) |
| Answerable from candidates | 16 / 18 |
| Answerable from admitted context | 15 / 18 |
| Authorized answers | 0 |
| False-answer rate | `0.0` |
| False-abstention rate on answerable examples | `1.0` |
| Decision accuracy | `0.375` |

The six hard negatives and three answerable examples whose context was incomplete all count in the
result. `p5dev_v1_query_010` had no gold support in the top three candidates;
`p5dev_v1_query_017` covered one of two gold claims; and `p5dev_v1_query_018` had all three claims
in the candidate set but the whole-item context budget admitted only two. This separates retrieval
loss from context-budget loss without treating chunk identity as proof of semantic correctness.

## Reproducibility and boundary

The machine-readable report is
[`phase5-development-single-review-v1-conservative-baseline.json`](../../reports/evaluation/phase5-development-single-review-v1-conservative-baseline.json)
with exact file SHA-256
`06e287491171a116cf18c4b899e8b90272596170e218ef86ed21aedf1d7359bb`.

It remains:

- single-review rather than independently adjudicated;
- exploratory development evidence rather than held out;
- structural chunk-support coverage rather than semantic support validation; and
- a baseline with `threshold_selected=false`, not permission to generate an answer.

Reproduce it with the command in the preregistration. The integration test rebuilds the report and
requires exact bytes from the versioned inputs.
