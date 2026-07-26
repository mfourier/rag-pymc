# Phase 5 development batch preregistration v1

## Status and scope

- Status: **Accepted — human preregistration review complete**
- Preregistration ID: `phase5-development-batch-preregistration-v1`
- Batch ID: `pymc-6.1.0-api-phase5-development-batch-v1`
- Annotation guidelines: `phase5-annotation-guidelines-v1`
- Adjudication guidelines: `phase5-adjudication-guidelines-v1`
- Intended dataset role: evidence-policy development only

This document fixes the design of the first Phase 5 development batch before candidate query
text, gold claims, or support sets are authored. It is not an accepted dataset, a held-out
evaluation set, a generation dataset, or evidence that any question is semantically
answerable. Candidate authors and reviewers must follow the existing
[Phase 5 annotation guidelines](phase5-development-annotation-guidelines-v1.md) in addition to
this preregistration.

Candidate annotation must not start while this status remains `Draft`. Human approval changes
the status to `Accepted` and records an opaque reviewer ID and a real UTC timestamp in the
approval record below. Any later change to counts, slot assignments, corpus identity, family
definitions, role separation, or leakage rules requires a new preregistration version and
another review before annotation resumes.

## Frozen evidence boundary

The batch is bound to the completed
[Gate A artifact](phase5-annotation-corpus-freeze-v1.md):

| Field | Fixed value |
|---|---|
| Annotation namespace | `pymc-6.1.0-api-phase5-development-v1` |
| Corpus role | `phase5-development-annotation` |
| Logical corpus path | `datasets/processed/phase5-annotation-api-v1` |
| Corpus hash policy | `canonical-chunk-identity-json-v1` |
| Corpus SHA-256 | `af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2` |
| Library and version | `pymc` `6.1.0` |
| Source type | `api_reference` |
| Parser and chunker | `sphinx-api-v1`; `api-reference-v1` |
| Documents and chunks | 4 documents; 15 chunks |

Only the generated API pages for `pymc.sample`, `pymc.Data`,
`pymc.model.core.set_data`, and `pymc.sample_posterior_predictive` are admissible evidence.
Conceptual notebooks, repository code, ArviZ, PyTensor, the Phase 4 final dataset, project
documentation, prompts, generated answers, and model memory are excluded.

Gate A was independently regenerated on 2026-07-25 in a temporary directory from the four
checked-in manifests and fixtures. The regenerated freeze record matched
`reports/evaluation/phase5-annotation-corpus-freeze-v1.json` byte for byte. This mechanical
check establishes corpus identity only; it does not establish semantic support.

## Fixed batch size and answerability target

The completed batch will contain exactly 24 accepted examples:

| Corpus-relative target | Count | Share |
|---|---:|---:|
| Answerable | 18 | 75% |
| In-library hard negative | 6 | 25% |
| Total | 24 | 100% |

The targets guide query construction; they do not override human judgment. If the frozen
corpus cannot support an intended answerable slot, the candidate must be revised or rejected.
It must not be labeled answerable merely to preserve a quota. A rejected candidate may be
replaced only by another candidate satisfying the same registered slot. If a slot cannot be
filled honestly, stop, revise this preregistration, and obtain new human approval.

All six unanswerable examples must be about PyMC and must be plausible near negatives for one
or more of the four admitted API symbols. Out-of-library questions are excluded because they
would not test the intended in-library evidence boundary. An unanswerable example contains no
gold claim or support set.

## Fixed coverage matrices

### Difficulty by answerability

Difficulty uses the existing `beginner`, `intermediate`, and `advanced` values.

| Difficulty | Answerable | Hard negative | Total |
|---|---:|---:|---:|
| Beginner | 7 | 1 | 8 |
| Intermediate | 9 | 3 | 12 |
| Advanced | 2 | 2 | 4 |
| Total | 18 | 6 | 24 |

Difficulty describes the reasoning and API-reading burden of the question, not retrieval
performance or the sophistication of a future generated answer.

### Intent by answerability

| Intent value | Answerable | Hard negative | Total |
|---|---:|---:|---:|
| `api_usage` | 6 | 1 | 7 |
| `parameter_behavior` | 5 | 1 | 6 |
| `return_and_storage` | 3 | 1 | 4 |
| `workflow_composition` | 3 | 1 | 4 |
| `version_sensitive` | 1 | 2 | 3 |
| Total | 18 | 6 | 24 |

These intent strings are annotation strata. They do not authorize query routing, generation,
or policy decisions.

### Query families

`query_family` identifies the semantic task. Every family ID below is reserved permanently
for development and must not be used in the future evidence-policy held-out set.

| Query family | Answerable | Hard negative | Total |
|---|---:|---:|---:|
| `sampling_controls` | 3 | 1 | 4 |
| `sampling_output_contract` | 2 | 1 | 3 |
| `data_container_contract` | 3 | 1 | 4 |
| `data_update_contract` | 3 | 1 | 4 |
| `posterior_predictive_controls` | 3 | 1 | 4 |
| `posterior_predictive_output_contract` | 1 | 0 | 1 |
| `mutable_prediction_workflow` | 3 | 1 | 4 |
| Total | 18 | 6 | 24 |

### Template families

`template_family` identifies the construction pattern, independent of the API symbol. The
future held-out set must use different template-family IDs and materially different patterns;
renaming one of these patterns does not make it disjoint.

| Template family | Construction pattern | Answerable | Hard negative | Total |
|---|---|---:|---:|---:|
| `direct_function_contract` | Ask for one documented purpose or behavior | 4 | 0 | 4 |
| `parameter_behavior` | Ask how a documented argument changes behavior | 4 | 0 | 4 |
| `input_constraint` | Ask about an admitted input, option, or compatibility constraint | 3 | 0 | 3 |
| `output_contract` | Ask about a documented return type, destination, or output condition | 3 | 0 | 3 |
| `procedural_workflow` | Ask for a bounded sequence using one or more admitted symbols | 4 | 0 | 4 |
| `unsupported_operation_contrast` | Ask for an operation not supported by nearby documentation | 0 | 3 | 3 |
| `unsupported_guarantee_contrast` | Ask for a guarantee not established by nearby documentation | 0 | 3 | 3 |
| Total |  | 18 | 6 | 24 |

### Expected API-symbol exposure

Counts are query-to-symbol memberships, not unique query counts. Four multi-symbol queries
produce 28 memberships across 24 examples. `expected_api_symbols` remains a routing aid and
does not substitute for human-reviewed support.

| Expected API symbol | Answerable memberships | Hard-negative memberships | Total memberships |
|---|---:|---:|---:|
| `pymc.sample` | 5 | 2 | 7 |
| `pymc.Data` | 5 | 2 | 7 |
| `pymc.model.core.set_data` | 6 | 1 | 7 |
| `pymc.sample_posterior_predictive` | 5 | 2 | 7 |
| Total | 21 | 7 | 28 |

### Claim complexity and boundary cases

| Claim structure | Answerable | Hard negative | Intended gold-claim count |
|---|---:|---:|---:|
| Single claim | 10 | 0 | 10 |
| Two claims | 6 | 0 | 12 |
| Three claims | 2 | 0 | 6 |
| No claims | 0 | 6 | 0 |
| Total | 18 | 6 | 28 |

Exactly four answerable slots are near-boundary cases. They must require complete support for
multiple necessary propositions and must be plausible candidates for evidence loss when only
a bounded rank prefix is admitted. They are selected from static corpus structure and query
design, not from observed retrieval rankings, context outcomes, evidence-policy scores, or
failures. The remaining 14 answerable slots are routine controls. All six unanswerable slots
are in-library hard negatives at the corpus boundary.

There is no preregistered quota for the number or cardinality of minimal support sets. Humans
must record every known semantically valid alternative minimal set for each claim. Quotas must
not be used to suppress alternatives or add redundant chunks.

## Registered construction slots

The candidate query ID must be the slot ID with `slot` replaced by `query`, for example
`p5dev_v1_query_001`. The table fixes design membership but deliberately contains no query
text, claim text, or chunk label.

| Slot | Target | Query family | Template family | Intent | Difficulty | Expected symbols | Claims | Boundary role |
|---|---|---|---|---|---|---|---:|---|
| `p5dev_v1_slot_001` | Answerable | `sampling_controls` | `direct_function_contract` | `api_usage` | Beginner | `pymc.sample` | 1 | Routine |
| `p5dev_v1_slot_002` | Answerable | `sampling_controls` | `parameter_behavior` | `parameter_behavior` | Beginner | `pymc.sample` | 1 | Routine |
| `p5dev_v1_slot_003` | Answerable | `sampling_controls` | `input_constraint` | `parameter_behavior` | Intermediate | `pymc.sample` | 2 | Routine |
| `p5dev_v1_slot_004` | Answerable | `sampling_output_contract` | `output_contract` | `return_and_storage` | Beginner | `pymc.sample` | 1 | Routine |
| `p5dev_v1_slot_005` | Answerable | `sampling_output_contract` | `input_constraint` | `version_sensitive` | Advanced | `pymc.sample` | 3 | Near-boundary answerable |
| `p5dev_v1_slot_006` | Answerable | `data_container_contract` | `direct_function_contract` | `api_usage` | Beginner | `pymc.Data` | 1 | Routine |
| `p5dev_v1_slot_007` | Answerable | `data_container_contract` | `parameter_behavior` | `parameter_behavior` | Beginner | `pymc.Data` | 1 | Routine |
| `p5dev_v1_slot_008` | Answerable | `data_container_contract` | `procedural_workflow` | `api_usage` | Intermediate | `pymc.Data` | 2 | Routine |
| `p5dev_v1_slot_009` | Answerable | `data_update_contract` | `direct_function_contract` | `api_usage` | Beginner | `pymc.model.core.set_data` | 1 | Routine |
| `p5dev_v1_slot_010` | Answerable | `data_update_contract` | `parameter_behavior` | `parameter_behavior` | Intermediate | `pymc.model.core.set_data` | 1 | Routine |
| `p5dev_v1_slot_011` | Answerable | `data_update_contract` | `procedural_workflow` | `api_usage` | Intermediate | `pymc.model.core.set_data` | 2 | Near-boundary answerable |
| `p5dev_v1_slot_012` | Answerable | `posterior_predictive_controls` | `direct_function_contract` | `api_usage` | Beginner | `pymc.sample_posterior_predictive` | 1 | Routine |
| `p5dev_v1_slot_013` | Answerable | `posterior_predictive_controls` | `parameter_behavior` | `parameter_behavior` | Intermediate | `pymc.sample_posterior_predictive` | 1 | Routine |
| `p5dev_v1_slot_014` | Answerable | `posterior_predictive_output_contract` | `output_contract` | `return_and_storage` | Intermediate | `pymc.sample_posterior_predictive` | 1 | Routine |
| `p5dev_v1_slot_015` | Answerable | `posterior_predictive_controls` | `output_contract` | `return_and_storage` | Intermediate | `pymc.sample_posterior_predictive` | 2 | Routine |
| `p5dev_v1_slot_016` | Answerable | `mutable_prediction_workflow` | `procedural_workflow` | `workflow_composition` | Intermediate | `pymc.Data`, `pymc.model.core.set_data` | 2 | Routine |
| `p5dev_v1_slot_017` | Answerable | `mutable_prediction_workflow` | `input_constraint` | `workflow_composition` | Advanced | `pymc.Data`, `pymc.model.core.set_data` | 2 | Near-boundary answerable |
| `p5dev_v1_slot_018` | Answerable | `mutable_prediction_workflow` | `procedural_workflow` | `workflow_composition` | Intermediate | `pymc.model.core.set_data`, `pymc.sample_posterior_predictive` | 3 | Near-boundary answerable |
| `p5dev_v1_slot_019` | Hard negative | `sampling_controls` | `unsupported_guarantee_contrast` | `version_sensitive` | Advanced | `pymc.sample` | 0 | In-library hard negative |
| `p5dev_v1_slot_020` | Hard negative | `sampling_output_contract` | `unsupported_operation_contrast` | `return_and_storage` | Intermediate | `pymc.sample` | 0 | In-library hard negative |
| `p5dev_v1_slot_021` | Hard negative | `data_container_contract` | `unsupported_guarantee_contrast` | `version_sensitive` | Advanced | `pymc.Data` | 0 | In-library hard negative |
| `p5dev_v1_slot_022` | Hard negative | `data_update_contract` | `unsupported_operation_contrast` | `api_usage` | Beginner | `pymc.model.core.set_data` | 0 | In-library hard negative |
| `p5dev_v1_slot_023` | Hard negative | `posterior_predictive_controls` | `unsupported_guarantee_contrast` | `parameter_behavior` | Intermediate | `pymc.sample_posterior_predictive` | 0 | In-library hard negative |
| `p5dev_v1_slot_024` | Hard negative | `mutable_prediction_workflow` | `unsupported_operation_contrast` | `workflow_composition` | Intermediate | `pymc.Data`, `pymc.sample_posterior_predictive` | 0 | In-library hard negative |

The fixed hard-negative category values are
`nearby-api-does-not-support-requested-operation` for slots 020, 022, and 024, and
`documented-options-do-not-establish-requested-guarantee` for slots 019, 021, and 023.

## Candidate and accepted artifact locations

The paths are fixed before candidate authoring:

| Artifact | Stable path | Authority |
|---|---|---|
| Agent-authored candidates | `datasets/evaluation/phase5/candidates/development-batch-v1.candidates.jsonl` | Draft only; never human ground truth |
| Deterministic review packet | `reports/evaluation/phase5-development-batch-v1-review.md` | Human-readable derivative of candidates and frozen corpus |
| Accepted dataset | `datasets/evaluation/phase5/development-v1.jsonl` | Only genuinely annotated and independently adjudicated records |
| Future Gate E validation record | `reports/evaluation/phase5-development-v1-validation.json` | Deterministic accepted-dataset audit |

The candidate file and review packet do not exist at preregistration time. Stage C may create
them only after this document is accepted. Candidate records must be visibly marked as drafts
outside the accepted path and must not claim `annotation.method=human` or
`adjudication.status=accepted` before the corresponding people have acted.

The review packet must be generated deterministically in query-ID order. For each candidate it
must show the slot assignments, query text, proposed corpus-relative label, proposed atomic
claims, every proposed minimal support set, and resolved chunk text with exact provenance. It
must not contain retriever ranks or scores, context-admission outcomes, policy signals,
thresholds, desired decisions, generated answers, or model judgments.

## Annotation and independent adjudication roles

1. An agent may draft candidate query text, decompose proposed claims, identify possible
   support sets, generate the review packet, and run deterministic validation. Agent work is
   proposal material, not human annotation.
2. At least one human annotator must author or explicitly accept the corpus-relative label,
   atomic claims, and minimal support sets for each example. Only opaque IDs such as
   `ann_001` may be persisted.
3. At least one different human adjudicator must independently review the complete example
   against the frozen corpus. Only opaque IDs such as `adj_001` may be persisted. No person
   may be both annotator and adjudicator for the same example.
4. Annotators and adjudicators may inspect the frozen corpus and resolved review packet, but
   must not inspect runtime policy scores, thresholds, retrieval outcomes, or desired policy
   decisions while assigning labels.
5. Annotation and adjudication use real UTC timestamps; adjudication cannot precede
   annotation. Reviewer IDs must not contain names, email addresses, prose, or secrets.
6. Disagreement is resolved by revising or rejecting the candidate, never by silently copying
   the candidate author's proposal. Only `accepted` adjudications enter the accepted JSONL.

The preregistration reviewer may later participate in annotation, but example-level annotator
and adjudicator independence remains mandatory. Availability of two genuinely distinct human
roles must be confirmed before Gate C begins.

## Leakage prevention and blinding

- The Phase 4 final 30-query dataset is excluded. Candidate text, claims, or labels must not be
  copied or paraphrased from it, and its measured retrieval or reranking outcomes must not be
  used to choose examples.
- Candidate authors start from the slot registry and frozen corpus, not from observed policy
  failures. No retrieval, context construction, or evidence policy is run until the accepted
  dataset is frozen.
- Before review, Stage C must perform an exact normalized-text duplicate check and a documented
  human near-duplicate review against prior evaluation queries. A flagged candidate is revised
  or rejected; it is not admitted based only on a low lexical-overlap score.
- All seven query-family IDs and seven template-family IDs in this document are
  development-only. The future evidence-policy held-out set must be prospectively authored
  after the signal, loss, threshold rule, and metrics are frozen, and must use semantically and
  structurally disjoint query and template families.
- The held-out set must not be created by splitting, sampling, paraphrasing, or minimally
  editing these 24 examples. Development outcomes must not be used to select held-out
  questions.
- If a future candidate resembles a development question despite different family labels,
  human semantic review takes precedence and the candidate is treated as leakage.

These rules reduce obvious leakage; they do not prove statistical independence in a small,
human-authored corpus.

## Annotation rules fixed before labels

For each intended answerable example:

- every proposition required for a minimally complete answer becomes an atomic gold claim;
- the final accepted claim count must match its registered slot;
- every claim has one or more nonempty alternative minimal chunk-support sets;
- every chunk resolves against the frozen PyMC 6.1.0 corpus;
- no support-set collection contains both a valid set and one of its strict supersets;
- background material, useful examples, and optional elaboration are excluded from support
  unless necessary for that claim.

For each intended hard negative:

- the corpus-relative label is `corpus_answerable=false` only after human review confirms that
  the frozen corpus cannot support every necessary proposition;
- `gold_claims` is empty;
- the registered hard-negative category is used;
- nearby or topically related chunks are not promoted into support.

No accepted record may contain runtime scores, retrieved IDs, context outcomes, budgets,
policy signals, thresholds, or policy decisions. The exact strict JSONL contract in the Phase
5 annotation guidelines remains authoritative.

## Fixed downstream measurements and non-measurements

After genuine adjudication and Gate E freezing, the unchanged conservative baseline will
record candidate and admitted-context claim coverage, support lost only to context budgeting,
retrieval or upstream-routing misses, answer coverage, selective risk, false-answer rate,
false-abstention rate, and decision accuracy under ADR-0011. Zero answer coverage is expected
and must not trigger relabeling or an ad hoc policy change.

This batch does not measure semantic answer correctness, citation correctness, citation
completeness, usefulness, pedagogy, or LLM behavior. It does not select an evidence signal,
loss function, answer-permitting threshold, prompt, model, or provider.

## Limitations registered before annotation

- The evidence corpus contains only four generated PyMC 6.1.0 API pages and is not
  representative of PyMC or Bayesian statistics as a whole.
- Conceptual, mathematical, diagnostic, implementation, ArviZ, PyTensor, and notebook-guided
  questions may be corpus-unanswerable even when they are valid library questions.
- API reference prose documents public behavior but does not necessarily teach complete
  workflows or explain implementation details.
- The 24-example batch is small. Slice counts will have high uncertainty and are intended for
  development diagnostics, not broad quality claims.
- Multi-symbol memberships are not independent observations, and equal membership totals do
  not imply equal semantic difficulty or evidence volume.
- Human adjudication can reduce but not eliminate annotation error. Exact chunk validation
  establishes identity and namespace consistency, not semantic sufficiency or minimality.
- Development-family disjointness and duplicate screening reduce obvious leakage but cannot
  prove independence from all prior human or model exposure.
- The batch is designed before runtime outcomes, so it may contain few or no actual
  context-budget failures. A null result must be reported rather than repaired post hoc.

## Human preregistration review decisions

The reviewer must explicitly approve or request revision for each item before candidate
annotation begins:

1. The 24-query size and 18/6 answerable-to-hard-negative balance.
2. The difficulty, intent, query-family, template-family, symbol, claim-complexity, and
   near-boundary matrices.
3. The realism and pedagogical value of the registered semantic and construction families.
4. The two hard-negative categories and the exclusion of out-of-library negatives.
5. The development-only family reservation and future held-out leakage rules.
6. The candidate, review-packet, accepted-dataset, and validation-record paths.
7. The annotation/adjudication role separation and availability of two distinct humans.
8. The API-only limitations and the rule that quotas never override corpus-relative human
   judgment.

### Approval record

| Field | Value |
|---|---|
| Decision | Accepted |
| Opaque preregistration reviewer ID | `mlioi` |
| Reviewed at (UTC) | `2026-07-26T03:40:07Z` |
| Requested revisions | None |
| Future role separation | `ann_001` and `adj_001` confirmed as distinct humans |

Do not infer approval from repository presence, a test pass, or agent review.

## Gate B exit criteria

Gate B is complete only when all of the following are true:

- the Gate A freeze has been regenerated from controlled inputs and still matches the checked-in
  artifact byte for byte;
- this document fixes exactly 24 construction slots and every coverage matrix reconciles to
  the slot registry;
- a qualified human has reviewed all eight decision points and the approval record contains an
  explicit `Accepted` decision, opaque reviewer ID, and real UTC timestamp;
- two distinct humans are confirmed as available for later example-level annotation and
  independent adjudication, without representing them as having reviewed data yet;
- no candidate query, accepted annotation, runtime retrieval result, context result, or policy
  score was used to tune this design;
- the candidate and accepted paths remain distinct and no accepted development JSONL has been
  created;
- limitations and leakage controls are accepted before candidate authoring starts;
- the repository documentation checks pass with no unexplained worktree changes.

The approval record is complete and Gate B is accepted. The next smallest unit, in a separate
iteration, is to draft the 24 candidates and produce the deterministic human-readable review
packet without creating an accepted dataset.
