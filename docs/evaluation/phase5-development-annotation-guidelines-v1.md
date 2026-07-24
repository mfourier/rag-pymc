# Phase 5 development annotation guidelines v1

## Purpose and boundary

These guidelines define how to author the first Phase 5 **development** dataset for evidence
coverage and abstention calibration. The file is not a held-out benchmark, a generation
dataset, or an answer-quality dataset. It measures whether an exact versioned corpus and a
runtime context contain adjudicated chunk support for atomic claims.

Use guideline versions `phase5-annotation-guidelines-v1` and
`phase5-adjudication-guidelines-v1`. Do not reuse the 30-query Phase 4 final set, inspect its
outcomes to choose Phase 5 labels, or later present the Phase 5 development set as untouched
evaluation evidence.

## Freeze the annotation corpus first

1. Build one deterministic processed corpus and load its validated `Chunk` records.
2. Compute its identity with `hash_phase5_corpus`. The policy is
   `canonical-chunk-identity-json-v1`, which hashes sorted chunk ID/content-hash records.
3. Put that exact policy and SHA-256 in every JSONL example.
4. Do not add, remove, rechunk, or edit sources during an annotation batch. Any corpus change
   requires a new hash, a new batch, and review of every support set.

The corpus used for initial calibration must be declared before annotation. The experimental
repository-code corpus must not silently enter the default documentation corpus; mixed-corpus
adoption still requires its own regression decision.

## Roles and blinding

- Use opaque reviewer IDs that contain no names, prose, email addresses, or secrets.
- At least one annotator authors the corpus-relative label and gold claims.
- At least one adjudicator independently reviews the complete record. An adjudicator cannot
  also be an annotator for the same example; the contract enforces this separation.
- Annotators and adjudicators may inspect the frozen corpus. They should not inspect candidate
  evidence-policy scores, thresholds, or desired policy outcomes while assigning gold labels.
- Record real UTC timestamps. Adjudication cannot precede annotation.

The JSONL file contains only records with adjudication status `accepted`. Drafts and reviewer
discussion belong outside the dataset artifact.

## Query construction

Author queries deliberately across multiple intents, difficulty levels, and template
families. Include:

- straightforward answerable API questions;
- multi-step questions whose answer requires more than one atomic claim;
- alternative phrasings that are not trivial string substitutions;
- near-boundary answerable questions where one necessary support chunk is easy to miss;
- in-library hard negatives about unsupported operations or guarantees;
- questions likely to expose budget omission, without selecting examples from observed policy
  failures alone.

`query_family` groups semantic tasks. `template_family` records the construction pattern so
near-duplicate templates remain visible. Do not randomly split templated paraphrases and call
the result independent evaluation data.

`expected_api_symbols` is a query-level routing aid, not a substitute for evidence. Store
unique symbols in lexicographic order. An empty tuple is valid when no public symbol is the
right expectation.

## Corpus answerability

Set `corpus_answerable=true` only when the frozen corpus contains enough evidence to support
every necessary atomic claim. This is not a judgment about whether the current retriever finds
that evidence or whether a generator is likely to answer correctly.

For an answerable example:

- provide at least one atomic gold claim;
- leave `hard_negative_category` null;
- provide one or more minimal support sets for every claim.

For an unanswerable example:

- provide no gold claims or support sets;
- use `hard_negative_category` when the query is an intentional near-negative, with a stable
  category such as `nearby-api-does-not-support-requested-operation`;
- do not invent a support set from semantically adjacent evidence.

## Atomic gold claims

A gold claim should express one independently assessable proposition needed by a minimally
complete answer. Split a sentence when one part could be supported while another is false or
unsupported. Do not turn headings, style requirements, optional examples, or pedagogical
elaboration into factual gold claims unless they are required by the question.

Claim IDs must be globally unique across the dataset. A recommended form is
`<query_id>_claim_<three-digit-number>`. Claim text is annotation content; it is not a required
surface form for a future generator.

## Minimal support sets

Each support set is a set of chunk IDs that jointly supports one atomic claim.

- A support set must be sufficient as a whole.
- It must be minimal: removing any member makes it insufficient for that claim.
- Store chunk IDs in lexicographic order with no duplicates.
- Record distinct alternative minimal sets when either alternative independently supports the
  claim.
- Do not record both a set and one of its strict supersets. The contract enforces this
  antichain rule.
- Do not combine chunks merely because they are useful background. Include only evidence
  necessary for the atomic claim.

The corpus validator resolves every referenced ID and rejects support chunks from another
library or version. It intentionally does not decide semantic sufficiency; that remains the
human annotation and adjudication responsibility.

## Record shape

Each nonblank JSONL line is one strict `phase5-development-annotation-v1` object. It must
contain no unknown fields, duplicate keys, non-finite numbers, runtime retrieval outcomes,
scores, thresholds, context budgets, or policy decisions. The dataset loader hashes the exact
raw file bytes; whitespace-only edits therefore create a new dataset identity.

Use one line per accepted example. Preserve a deliberate stable order, but do not interpret
file order as a ranking. The loader rejects duplicate query IDs, globally duplicate claim IDs,
mixed corpus hashes, invalid UTF-8, and unsupported schema values.

## Required validation gate

Before a batch is frozen:

1. Load the JSONL with `load_phase5_development_dataset`.
2. Load the exact processed corpus and call `validate_phase5_development_corpus`.
   `rag-pymc validate-development-data --dataset <path> --corpus-dir <path>` performs both
   operations and emits the canonical audit record.
3. Confirm the returned dataset hash, corpus hash, chunk count, gold claim count, support-set
   count, and referenced chunk IDs against the batch record.
4. Resolve a human-readable view of every support set and have an independent adjudicator
   accept, revise, or reject it.
5. Re-run the loader, corpus validator, static checks, and tests after the final byte change.
6. Only then run `phase5-gold-evidence-v1` over a fixed retrieval/context/policy configuration.

The conservative policy baseline should produce zero answer coverage. Complete gold contexts
that it refuses are measured as unnecessary abstentions; this expected result documents the
starting safety boundary and does not authorize an ad hoc threshold.

## Metrics fixed before annotation

ADR-0011 fixes answer coverage, selective risk, false-answer rate, false-abstention rate,
decision accuracy, candidate claim coverage, and admitted-context claim coverage. Conditional
rates are `null` when their denominator is zero. Do not alter labels to improve these metrics,
and do not add a threshold after inspecting the same data without a predeclared signal,
asymmetric loss, and deterministic selection rule.

## Exit criteria for the first development batch

The batch is ready for policy-development experiments only when:

- all records pass strict JSONL loading and corpus validation;
- every answerable query has adjudicated atomic claims and minimal support sets;
- every adjudicator is independent from that example's annotators;
- query/template families and hard-negative categories have been reviewed for accidental
  duplication or leakage;
- the exact corpus and dataset SHA-256 values are recorded;
- no example contains runtime scores, retrieved IDs, context outcomes, or policy decisions;
- limitations and coverage gaps are documented before threshold work begins.

An untouched Phase 5 evaluation set must be authored later, after the evidence signal,
asymmetric loss, threshold rule, and metrics are frozen. It must not be split retrospectively
from policy-development outcomes.
