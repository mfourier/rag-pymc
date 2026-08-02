# PyMC 6.2.0 controlled migration v1

## Decision

The active four-page API corpus and optional scientific runtime now target PyMC 6.2.0. The
migration changes no source breadth, retriever, chunker, tokenizer, context policy, or sufficiency
policy. It was executed under the
[`pymc-6.2.0-controlled-migration-preregistration-v1.md`](pymc-6.2.0-controlled-migration-preregistration-v1.md)
gate.

The official release is `v6.2.0` at upstream commit
`3b661c7e5e3ca7d5d7550eca36991d7c1e72274e`. Each controlled fixture was acquired from its official
generated API detail page, required to identify itself as PyMC 6.2.0, and frozen with its own
manifest and exact raw-byte SHA-256.

## Source and normalized comparison

| API symbol | PyMC 6.2.0 raw SHA-256 | Normalized result |
| --- | --- | --- |
| `pymc.Data` | `ba15eba8195925d28dd0234a05f7807f4219c9c33871e4e136da5b60f6861e82` | exact match |
| `pymc.model.core.set_data` | `14eb483a1bc93fa7b9a628a58eb336872d603203a14a40659f5752c44394144a` | exact match |
| `pymc.sample` | `08153ae8af4c7a869135747b34a57f674b7f32e3a4c78d47de4fc94046caf559` | exact match |
| `pymc.sample_posterior_predictive` | `cb7d4b34c27ce68f35a157dc18380bce99e4d6e8e00e41551ab154b805ed21ed` | exact match |

All four raw files differ from their 6.1.0 counterparts, while all four parsed documents and all
15 chunks are exact normalized matches. All 10 chunks referenced by the Phase 5 review and all 31
minimal support sets map exactly. This is strong mechanical compatibility evidence for the narrow
slice, but it is neither complete PyMC coverage nor a new human review.

## Corpus identity correction

The historical `canonical-chunk-identity-json-v1` policy hashes only sorted chunk IDs and content
hashes. Because the normalized chunks did not change, it produces the same legacy hash
`af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2` for both releases. That value
is useful for content equivalence but insufficient as a release identity.

The 6.2.0 freeze therefore uses `canonical-corpus-provenance-json-v2`. It binds library/version,
release tag, upstream commit, exact source manifests and raw hashes, parsed documents, and chunks.
Its corpus SHA-256 is
`796e7aee3f1fae1423bc04f0478381e6f7338afdd85d2f3a9d1d9cfa692c573a`. The old v1 policy and all
historical 6.1.0 artifacts remain unchanged.

## Retrieval comparison

The Phase 4 retrieval dataset was projected mechanically by changing only PyMC query versions after
exact normalized document/chunk validation. Its 30 queries include 27 PyMC 6.2.0-answerable cases
and preserve the three cross-library or unanswerable controls. The projected dataset explicitly
records `new_human_judgment=false`, `held_out=false`, and `threshold_selected=false`.

At `top_k=3`, `k1=1.5`, and `b=0.75`, every ranking and non-latency aggregate matches the historical
6.1.0 run:

| Metric | Result |
| --- | ---: |
| Recall@3 | `0.925926` |
| MRR | `0.771605` |
| nDCG@3 | `0.811723` |
| Unanswerable empty-result rate | `0.666667` |
| Version correctness | `1.0` |

Latency is intentionally excluded from exact comparison because it is machine-specific.

## Artifacts and reproduction

- [provenance-complete 6.2.0 freeze](../../reports/evaluation/pymc-6.2.0-api-v1-freeze.json)
- [6.1.0 to 6.2.0 migration report](../../reports/evaluation/pymc-6.1.0-to-6.2.0-migration-v1.json)
- [projected retrieval dataset](../../datasets/evaluation/migrations/pymc-6.2.0-phase4-exact-projection-v1.jsonl)
- [projection provenance report](../../reports/evaluation/pymc-6.2.0-phase4-exact-projection-v1.json)
- [BM25 migration diagnostic](../../reports/evaluation/pymc-6.2.0-bm25-migration-v1.json)

The internal research CLI exposes `freeze-controlled-api-corpus`,
`compare-pymc-620-migration`, and `project-pymc-620-retrieval-dataset`. The migration integration
test rebuilds the two corpora from checked-in fixtures, requires exact freeze/migration/projection
bytes, and compares all retrieval fields except latency.

The next corpus increase must be a separately preregistered PyMC-only API batch. The public API
index may guide symbol selection, but every admitted detail page requires an exact fixture,
manifest, provenance freeze, retrieval evaluation, and renewed human support review wherever
normalized evidence changes.
