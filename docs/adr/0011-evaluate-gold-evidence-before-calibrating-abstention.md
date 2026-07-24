# ADR-0011: Evaluate gold evidence before calibrating abstention

- Status: Accepted
- Date: 2026-07-24

## Context

ADR-0009 requires a separate Phase 5 development dataset before any answer-permitting
evidence policy or threshold is selected. Retrieval qrels are insufficient for this purpose:
one answer can contain several atomic claims, and one claim may require multiple chunks
jointly or admit several alternative minimal support sets. Context budgeting can also remove
evidence that retrieval found, so a single relevant-chunk hit cannot distinguish retrieval
failure from budget loss.

The development annotation and deterministic JSONL-loading contracts represent
corpus-relative answerability, atomic gold claims, alternative minimal support sets, query
families, hard negatives, and human annotation/adjudication provenance. Before authoring the
dataset, the metrics and their denominators must be fixed so labels are not designed around a
preferred policy result.

## Decision

Bind annotations to `canonical-chunk-identity-json-v1`: canonical JSON over records containing
each unique chunk ID and its content SHA-256, sorted by chunk ID and hashed as ASCII. Before
evaluating a dataset, require the declared hash to match the available nonempty corpus,
resolve every gold support-set ID, and require every referenced chunk to match the annotated
library and version. This validation fails before policy metrics are computed.

Implement the pure evaluator `phase5-gold-evidence-v1`. It accepts one validated development
annotation, one `ConstructedContext`, one `EvidenceAssessment`, and the SHA-256 identity of
the runtime corpus. It rejects mismatched corpus, query text, library, library version,
included chunk IDs, or omitted chunk IDs.

For each atomic gold claim, evaluate whether at least one complete minimal support set is
contained in:

1. the budget-admitted context chunk IDs; and
2. the candidate IDs, defined as admitted IDs plus the rank-prefix tail omitted by the
   context budget.

A corpus-answerable query is gold-answerable from a context only when every atomic gold claim
has at least one support set wholly present in the admitted context. Candidate answerability
uses the same rule over admitted plus omitted IDs. A corpus-unanswerable query is never
gold-answerable merely because nearby chunks were retrieved. Candidate-answerable but
context-unanswerable cases are classified as budget-prevented answerability; cases that are
not candidate-answerable remain retrieval or upstream-routing misses at this boundary.

Score the policy decision against gold context answerability:

- authorizing an answer without complete gold context is an unsupported answer;
- abstaining with complete gold context is an unnecessary abstention;
- all other decisions are correct at this evidence-presence boundary.

Aggregate exactly one result for every development query, require a single corpus and policy
version, canonically order results by query ID, and recompute every claim match from the gold
annotations before accepting a report. Record the canonical context hash without copying
context content into the report.

Fix the aggregate denominators as follows:

- answer coverage: authorized answers divided by all queries;
- selective risk: unsupported authorized answers divided by authorized answers;
- false-answer rate: unsupported authorized answers divided by gold-context-unanswerable
  queries;
- false-abstention rate: unnecessary abstentions divided by gold-context-answerable queries;
- decision accuracy: correct evidence decisions divided by all queries;
- context and candidate claim coverage: covered gold claims divided by all gold claims.

Return `null` when a conditional denominator is zero. Do not replace an undefined rate with
zero. Preserve counts alongside every rate.

These measurements establish only whether adjudicated chunk identities are present. They do
not evaluate generated prose, semantic claim correctness, citation correctness, citation
completeness, pedagogy, or whether the annotations themselves are scientifically sound. The
evaluator does not select a threshold or asymmetric loss and does not authorize generation.

## Alternatives considered

### Treat any relevant chunk as sufficient

Rejected because an answer can require several claims or a jointly sufficient set of chunks.
One relevant hit can leave material claims unsupported.

### Evaluate only the final admitted context

Rejected because it would confound a retrieval miss with a budget policy that removed
otherwise sufficient candidates. Both are failures for the end-to-end system but require
different interventions.

### Use corpus answerability as the expected runtime decision

Rejected because a corpus can contain a complete answer while the actual retrieved and
budgeted context does not. Authorizing generation in that case would expose the generator to
insufficient evidence.

### Score generated claim text now

Rejected because there is no generator, prompt-safe serialization, claim-alignment contract,
or validated semantic judge. Exact chunk-identity coverage is narrower but deterministic and
auditable.

## Consequences

- Development annotations can be authored against fixed metrics rather than post-hoc policy
  outcomes.
- A dataset cannot pass the evaluation gate with a stale corpus hash, duplicate corpus chunk
  identity, missing gold reference, or cross-library/version support set.
- Retrieval loss and budget loss are visible separately at claim and query level.
- Unsafe authorization and conservative over-abstention have explicit counts and rates.
- The current conservative policy is expected to show zero answer coverage and unnecessary
  abstention whenever complete gold context is present; that is a baseline result, not a
  reason to weaken it without calibration.
- Any answer-permitting policy still requires a versioned signal contract, a predeclared
  asymmetric loss, deterministic selection behavior, and an untouched held-out evaluation
  set.
- Semantic generation and citation-quality evaluators remain later Phase 5 work.
