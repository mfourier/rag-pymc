# ADR-0010: Separate versioned repository code from documentation

- Status: Accepted
- Date: 2026-07-23

## Context

The controlled corpus answers public API questions from four generated PyMC 6.1.0 pages.
Those pages are the appropriate source for documented behavior, parameters, return values, and
examples, but they do not expose enough evidence for implementation questions such as sampler
dispatch, graph mutation, or posterior-predictive variable selection.

A local PyMC clone is available at release `v6.2.0`. The `rag-pymc` runtime and evaluation
baseline remain pinned to PyMC 6.1.0. The clone contains the immutable `v6.1.0` tag at commit
`56384e5afed6d1ad122e19b1bf3a7885fc38e5e5`, so exact 6.1.0 files can be acquired without
changing the upstream checkout.

Copying the checkout working tree would silently introduce PyMC 6.2.0. Indexing the complete
repository would also mix public implementation, tests, generated files, and unrelated
subsystems before retrieval behavior had been measured.

## Decision

Add an experimental `repository_code` corpus as a separate, versioned evidence layer. Its
first vertical slice covers the same public symbols as the frozen Phase 4 API corpus:

- `pymc.sample` from `pymc/sampling/mcmc.py`;
- `pymc.Data` from `pymc/data.py`;
- `pymc.model.core.set_data` from `pymc/model/core.py`;
- `pymc.sample_posterior_predictive` from `pymc/sampling/forward.py`.

Acquire complete files from the exact Git tag. Give each selected symbol its own manifest with
the repository path, commit, tag, raw hash, timestamps, media type, expected public symbol, and
license. Verify raw bytes before parsing.

Parse Python with the standard-library AST. Select the final non-overload top-level
implementation, preserve its exact line span and signature, and split its body only between
top-level statements. Store a short docstring summary in the definition chunk; leave detailed
documentation in the API-reference corpus to avoid duplicate evidence. Bound grouped code
payloads while never splitting an individual statement.

Keep `datasets/processed/repository-code` and any mixed corpus experimental. Do not replace the
Phase 4 corpus or selected retrieval policy until a versioned evaluation measures
implementation queries and regression on the original documentation queries.

Do not ingest upstream tests yet. Before doing so, extend provenance with an explicit role such
as `implementation` or `upstream_test`; a test demonstrates asserted behavior but is not a
public API guarantee.

## Alternatives considered

### Index the active checkout

Rejected because the checkout is PyMC 6.2.0 and would violate the 6.1.0 runtime boundary.

### Index every file at `v6.1.0`

Rejected for the first experiment because unrelated internals, tests, and generated content
would add retrieval noise without a measured need.

### Copy only extracted function snippets

Rejected as the acquisition artifact because a derived snippet is harder to verify against
upstream. Complete files are snapshotted and hash-verified; parser output selects the symbol.

### Mix code into Phase 4 immediately

Rejected because it would invalidate the frozen baseline and make quality changes impossible to
attribute.

## Consequences

- Implementation questions can retrieve exact PyMC 6.1.0 code with line spans and public-symbol
  metadata.
- Documentation and implementation can be filtered independently by `source_type`.
- The local 6.2.0 working tree cannot leak into the 6.1.0 corpus through the snapshot command.
- AST chunks remain source fragments, not standalone executable programs.
- Complete source files increase repository size modestly but preserve byte-level auditability.
- Adoption into default mixed retrieval requires a new comparison report and no material
  regression on Phase 4 documentation queries.
