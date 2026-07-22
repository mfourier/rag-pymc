# ADR-0008: Define deterministic context construction

- Status: Accepted
- Date: 2026-07-21

## Context

Phase 4 selects equal-weight Reciprocal Rank Fusion as the default retrieval policy, but a
ranked list of chunks is not yet a bounded, inspectable input for grounded response
generation. Phase 5 first needs to establish how retrieved evidence is ordered, represented,
deduplicated, and admitted under a budget. Connecting an LLM before fixing those rules would
couple provider-specific tokenization and prompting decisions to the evidence boundary and
would make context changes difficult to attribute or reproduce.

The context artifact must retain the provenance required to inspect a future answer: chunk
and document identity, exact source URL, section, library version, API symbols, and content.
Budget accounting must include this metadata because it will be visible to a future generator
and consumes space alongside the evidence itself. The policy also needs explicit behavior
when a high-ranked chunk does not fit, especially because several current chunks exceed the
fixed embedding model's input limit and technical chunks can contain indivisible code or
statistical explanations.

Context construction is not evidence-sufficiency assessment. Retrieval rank and the presence
of one or more chunks do not establish that the corpus supports an answer.

## Decision

Define project-owned domain contracts for a context item and a constructed context, plus a
provider-neutral `ContextBuilder` boundary. Keep those contracts independent of filesystems,
LLM SDKs, prompt frameworks, and model tokenizers. The builder accepts one `SearchQuery`, a
sequence of `RetrievedChunk` values, and an explicit positive budget.

Canonicalize candidates before budgeting as follows:

1. Sort candidates by retrieval `rank`, then by `chunk_id` for deterministic ties.
2. For repeated `chunk_id` values with identical chunk payloads, retain the first canonical
   occurrence. If duplicate results have both the same rank and chunk ID, use the retriever
   name as a tertiary tie-break so input sequence order cannot change the retained strategy.
3. Reject repeated `chunk_id` values whose chunk payloads conflict instead of silently
   selecting one.

Deduplication is by `chunk_id`, not by `document_id` or `source_url`. Distinct chunks and
sections from the same source are valid evidence and remain eligible for inclusion.

Render every context item through an explicit, versioned canonical representation for
accounting and inspection. The representation preserves at least `chunk_id`, `document_id`,
`source_url`, `section`, `library_version`, `api_symbols`, retrieval rank and strategy, and
chunk content. Store the context schema and builder/rendering policy versions in the result
so the same inputs and configuration can reproduce the same artifact. Do not add timestamps,
latency, or other run-dependent fields to this domain value.

The structured `ContextItem` and `ConstructedContext` JSON fields are authoritative.
`rendered_text` is derived from those fields and exists only for deterministic accounting and
inspection. It is not a prompt, a trusted generator framing, or a security boundary. It does
not escape content or protect delimiters from instructions contained in source text. A future
provider and prompt-versioning ADR must define prompt-safe framed and escaped serialization
before any generator consumes context.

Inject a project-owned token-counter protocol with an explicit counter name and version.
Use `technical-v1` as the first deterministic baseline. It counts the complete canonical
rendering of each item, including provenance metadata and content. `technical-v1` is a
project accounting heuristic, not an LLM tokenizer, and its counts must not be interpreted as
the input-token count of any future provider or model. Version 1 defines aggregate usage as
the sum of standalone rendered-item counts; it does not claim equivalence with tokenizing a
future joined prompt using a provider's subword tokenizer.

Before budgeting, reject candidates that conflict with an explicit query library or library
version. Also reject a candidate set spanning more than one normalized library, and reject
multiple versions of the same library. Until a cross-library compatibility policy exists,
context v1 therefore cannot combine PyMC, ArviZ, and PyTensor evidence. These checks keep
context construction from silently crossing library or version boundaries even if an upstream
retriever is misconfigured.

Apply a complete-item, rank-prefix budget policy. Visit the canonical candidates in order and
include an item only when its complete rendered representation fits in the remaining budget.
At the first non-fitting item, stop construction and record that item and the remaining
canonical tail as omitted, in order. Do not skip the item to pack shorter, lower-ranked
candidates, and do not truncate within a chunk. Report the configured budget, total used
count, per-item counts, included IDs, and omitted IDs in the constructed context.

An empty context is a valid deterministic result, including when the first candidate exceeds
the budget or retrieval returns no candidates. Neither an empty nor a nonempty result decides
evidence sufficiency. A separate `AbstentionPolicy` will later assess whether the available
evidence supports answering.

This decision does not yet add citations, grounded answer sections, a generator, an
abstention threshold, or a CLI command. Those components must consume the context contract in
later, separately testable changes.

## Alternatives considered

### Use an LLM provider's tokenizer now

A provider tokenizer could approximate a future prompt limit more closely, but it would
prematurely bind context construction to a model family and make offline tests dependent on
provider assets. The injected counter boundary permits a model-specific implementation after
the generator and prompt versions are selected.

### Count only chunk content

This would be simpler, but it would undercount source identity and other metadata that a
grounded generator must receive. Counting the canonical rendered item accounts for the same
metadata and evidence preserved by the structured artifact.

### Truncate a chunk to consume the remaining budget

Character- or token-level truncation could increase nominal utilization, but it can split
code blocks, signatures, warnings, or statistical explanations and obscure whether the
resulting excerpt is meaningful. Complete chunks preserve the structure produced by the
versioned chunker. A future structure-aware truncation policy would require its own explicit
decision and evaluation.

### Skip a non-fitting item and continue packing shorter candidates

This can use more of the budget, but it allows chunk length to reorder the evidence selected
by retrieval and produces a non-prefix of the ranking. Stopping at the first non-fitting item
preserves the retrieval policy's priority and makes omissions straightforward to inspect.

### Deduplicate by document or source URL

This would reduce repeated provenance metadata, but it would discard distinct API sections or
examples from the same official page. Chunk identity is the appropriate unit because it
preserves structure-aware evidence while still rejecting conflicting duplicates.

### Treat any retrieved context as sufficient evidence

Ranked retrieval always returns the nearest available chunks for many in-library unsupported
questions. Presence alone would repeat the known Phase 4 abstention failure. Sufficiency and
threshold selection require a separate development dataset and policy.

## Consequences

- Context artifacts are deterministic and traceable for fixed query, candidates, policy
  versions, counter, and budget.
- Every included item accounts for both its evidence content and the provenance needed for
  later citation and version checks.
- Conflicting payloads fail explicitly, while multiple useful sections from one source remain
  available.
- The rank-prefix rule preserves retrieval priority but can leave budget unused and omit
  shorter lower-ranked evidence.
- Complete-item admission avoids damaged code and explanations, but one oversized top-ranked
  chunk can yield an empty context even when later chunks would fit.
- `technical-v1` provides reproducible offline accounting but cannot guarantee compliance
  with a future model's actual context window. A provider/model-specific counter will require
  versioned integration and comparison.
- Context v1 rejects candidate sets spanning more than one normalized library. A compatibility
  contract must be fixed before mixed PyMC, ArviZ, and PyTensor context is admitted.
- Structured context fields are authoritative. `rendered_text` remains a derived accounting
  and inspection value, not prompt-safe framing; a provider and prompt-versioning ADR must
  define escaping and framing before generation.
- The domain models validate canonical rendering and aggregate arithmetic, while the builder
  executes the configured counter. Hydrating an artifact from an untrusted external JSON
  source would still require recomputing its per-item counts through that named counter; no
  such persistence boundary is introduced in this slice.
- Context construction exposes what evidence is available; it does not validate claims,
  produce citations, or decide whether to answer.
- Citation correctness and completeness, unsupported-claim evaluation, generator behavior,
  abstention threshold selection, and CLI inspection remain subsequent Phase 5 units.
