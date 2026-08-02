# PyMC 6.2.0 controlled migration preregistration v1

## Status and scope

- Status: fixed before corpus construction and retrieval evaluation
- Release: `v6.2.0`
- Source commit: `3b661c7e5e3ca7d5d7550eca36991d7c1e72274e`
- Migration role: version adoption experiment

This work migrates exactly the four API symbols in the active PyMC 6.1.0 corpus. It does not expand
symbol breadth, add a retriever, select a sufficiency threshold, or reinterpret the existing human
review as a PyMC 6.2.0 review.

The Phase 5 PyMC 6.1.0 corpus, decisions, dataset, and conservative baseline remain immutable
historical evidence. PyMC 6.2.0 receives new fixtures, manifests, document and chunk identities,
corpus hashes, environment pins, defaults, and reports.

## Fixed sources

| Symbol | Official acquisition URL |
| --- | --- |
| `pymc.Data` | `https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.Data.html` |
| `pymc.model.core.set_data` | `https://www.pymc.io/projects/docs/en/stable/api/model/generated/pymc.model.core.set_data.html` |
| `pymc.sample` | `https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html` |
| `pymc.sample_posterior_predictive` | `https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample_posterior_predictive.html` |

The stable URLs are admitted only when every downloaded page identifies itself as PyMC 6.2.0 and
is frozen by an exact raw-byte SHA-256. The manifests bind those bytes to release tag `v6.2.0`, the
release commit above, Apache-2.0 licensing, and a real UTC acquisition timestamp. A future change to
the moving stable URL cannot alter the checked-in fixture.

## Fixed implementation policy

1. Exercise `sphinx-api-v1` and `api-reference-v1` unchanged first.
2. Fail closed if a page has no exact expected API symbol or semantic sections.
3. Build a separate `pymc-6.2.0-api-v1` corpus; never upsert into the 6.1.0 snapshot.
4. Compare normalized documents and chunks by symbol and section, not raw HTML alone.
5. Record added, removed, and changed normalized sections and support-set mapping coverage.
6. Keep BM25 `k1=1.5`, `b=0.75`, `top_k=3`, `technical-v1`, and the 2048-unit context policy for
   the controlled retrieval comparison.
7. Do not copy the 6.1.0 dataset into a human-reviewed 6.2.0 dataset. Mechanical projections must
   remain visibly non-human and cannot authorize calibration.

## Adoption criteria

- all four sources pass manifest integrity, parser, chunker, parent-reference, library, and version
  validation;
- the new corpus and freeze reproduce byte for byte from checked-in inputs;
- normalized semantic changes are reported explicitly;
- Phase 4 retrieval queries are evaluated against both versions without changing query text or
  relevance judgments, and the comparison is labeled a version migration diagnostic;
- runtime and optional scientific dependencies resolve and the full offline suite passes;
- documentation defaults identify 6.2.0 while retaining the 6.1.0 reproduction paths; and
- no 6.2.0 sufficiency threshold or human-reviewed support dataset is claimed without a new review.

## Human boundary

Any claim whose supporting normalized text changed, disappeared, split, or merged requires renewed
human review before it can enter a PyMC 6.2.0 gold dataset. Even exact-text mechanical mappings are
reported as migration evidence rather than a new human decision.
