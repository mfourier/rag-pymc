# ADR-0009: Fail closed with a conservative no-threshold evidence policy

- Status: Accepted
- Date: 2026-07-21

## Context

ADR-0008 defines a deterministic context artifact but deliberately does not infer that
retrieved evidence is sufficient to answer. The Phase 5.2 inspection command exposes that
artifact without generating an answer. Phase 5 now needs a stable boundary between context
construction and any future generator so the absence of a calibrated policy cannot silently
be interpreted as permission to answer.

Retrieval presence is not an evidence-sufficiency signal. Rankers return the nearest available
chunks for unsupported in-library questions, while metadata filters can produce an empty
result for out-of-library questions. A context can also be empty because the highest-ranked
complete item exceeds its explicit budget. Those outcomes require different diagnostics even
though none permits grounded generation.

The final Phase 4 dataset at
`datasets/evaluation/phase4/pymc_core_queries.jsonl` has SHA-256
`5f5eb1f0e42a77759a5a1b33bae26fa43264002238633ed93a3d0d6695aa454b`. It contains 30
queries: 27 answerable and three unanswerable. Two unanswerable questions are excluded by
library metadata, leaving one unsupported in-library question that reaches retrieval. The
dataset has already been used to select equal-weight RRF, evaluate the cross-encoder, and
inspect the cross-encoder logits for that unsupported question. It is a final evaluation set,
not a threshold-development set.

## Decision

Define immutable provider-neutral domain values:

- `EvidenceSufficiency` with `sufficient`, `insufficient`, and `not_assessed`;
- `EvidenceAssessment` with a schema version, policy version, sufficiency value, explicit
  abstention decision, deterministic reason codes, included context chunk IDs, and omitted
  chunk IDs.

An assessment abstains unless sufficiency is explicitly `sufficient`. `not_assessed` is
therefore fail-closed, not an alias for sufficient. Reason codes and chunk identities are
unique and deterministic, included and omitted IDs cannot overlap, and the model contains no
score, threshold, confidence, timestamp, or latency field.

Add a project-owned `AbstentionPolicy` protocol and implement
`ConservativeAbstentionPolicy` with policy identity `conservative-no-threshold-v1`. It copies
the exact included and omitted chunk IDs from `ConstructedContext` and applies only structural
rules:

1. No included or omitted IDs produces `insufficient`, abstains, and records
   `no_retrieved_evidence`.
2. No included IDs with an omitted tail produces `insufficient`, abstains, and records
   `budget_excluded_all_evidence`.
3. Any nonempty context produces `not_assessed`, abstains, and records
   `no_calibrated_criterion`.
4. A nonempty context with an omitted tail additionally records
   `budget_omitted_evidence`.

The conservative policy never returns `sufficient` and consequently has zero answer coverage.
That outcome is intentional: this slice establishes a safety boundary and traceable reason
codes, not a useful calibrated answering policy or an abstention-quality result. Invalid
inputs or policy failures must propagate as errors; a future orchestration layer must not
fall back to answering when no valid sufficient assessment exists.

Do not select a numeric threshold from the Phase 4 final dataset. Do not infer sufficiency
from context nonemptiness, retrieval rank, RRF score, item count, complete budget admission,
metadata compatibility, or cross-encoder logits. `ConstructedContext` intentionally does not
carry retrieval scores. A future score-based policy requires a separate versioned signal
contract rather than adding an uncalibrated value to this policy or reinterpreting context v1.

Future threshold selection requires, before implementation:

1. A separately authored and frozen development dataset that is not split from the observed
   Phase 4 final set.
2. More hard in-library negatives, near-boundary answerable cases, multiple intents, and
   contexts affected by budget omission.
3. Human-reviewed corpus-relative sufficiency labels for the exact retrieved and constructed
   evidence, not retrieval qrels alone.
4. A fixed inference-time signal contract with model or algorithm identity, corpus hash,
   retrieval configuration, context-policy version, and token budget.
5. A predeclared asymmetric loss that treats unsupported answers as more costly than
   unnecessary abstentions, plus fixed coverage, selective-risk, false-answer, and
   false-abstention metrics.
6. A deterministic threshold-selection rule, including equality and tie behavior, with
   per-query signals and decisions stored in a reproducible development report.
7. An untouched Phase 5 evaluation set used only after the threshold, policy, and metrics are
   frozen.
8. Recalibration whenever the corpus, retriever, reranker, context policy, budget, or
   score-producing model changes.

## Alternatives considered

### Treat every nonempty context as sufficient

This would provide immediate answer coverage but repeats the known Phase 4 failure: the
selected retriever returns PyMC chunks for an unsupported in-library question. Retrieval
presence is necessary for a grounded answer but does not establish semantic support.

### Permit answers when no evidence was omitted by the budget

A complete rank prefix only establishes that selected chunks fit the accounting budget. It
does not show that those chunks answer the question, and lower-ranked relevant evidence may
still be absent from retrieval.

### Tune an RRF score threshold on the Phase 4 dataset

RRF scores are configuration-dependent rank-fusion values rather than calibrated
probabilities. Selecting a cutoff after observing the final results would overfit the only
benchmark and would be informed by only one in-library unsupported question.

### Tune a threshold from the cross-encoder logits

The raw logits are uncalibrated, the model reduced aggregate retrieval quality, and the
unsupported query's negative logits were already inspected. Choosing a threshold from that
observation would be post-hoc leakage explicitly prohibited by ADR-0007.

### Use lexical or API-symbol overlap

Surface overlap is brittle for technical aliases such as `pymc.set_data` and
`pymc.model.core.set_data`, and a query can repeat an API name without the retrieved section
supporting its requested claim. This heuristic has no controlled development evaluation.

### Ask a generator to assess its own evidence

This would couple the safety boundary to one provider, prompt, and stochastic judgment before
prompt-safe framing or generation contracts exist. It would also make the component that
produces claims responsible for deciding whether those claims are supported.

### Train a sufficiency classifier now

There is no separate labeled training or development dataset. Training or model selection on
the final 30-query set would invalidate subsequent evaluation.

## Consequences

- Evidence assessment is a project-owned, deterministic boundary independent of LLM SDKs and
  retrieval implementations.
- Empty retrieval and complete budget exclusion both abstain but retain different actionable
  reasons.
- Partial and complete nonempty contexts remain explicitly unassessed and cannot authorize
  an answer.
- The policy has zero answer coverage and is not evidence that abstention quality is good.
- No score, threshold, confidence, or measured quality claim is introduced in this slice.
- The boundary can be exercised with deterministic tests and fakes before generation exists.
- A future calibrated policy can use the `sufficient` state, but only through a new versioned
  implementation and the development process fixed above.
- A richer inference signal, threshold selection, calibration report, held-out evaluation,
  semantic claim-support evaluation, prompt-safe serialization, and provider-backed
  generation remain deferred. Citation and generator-boundary contracts plus structural
  traceability were implemented in later Phase 5 slices without changing this policy.
