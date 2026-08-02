# Phase 5 and PyMC 6.2.0 checkpoint closure v1

## Closure result

The Phase 5 single-human exploratory review, its conservative baseline, and the controlled PyMC
6.1.0 to 6.2.0 migration form one reproducible historical checkpoint. This record closes their
engineering audit before MCP work; it does not convert the dataset into independent adjudication,
held-out evidence, production-grade evidence, or permission to select a sufficiency threshold.

Revalidation ran on branch `main` at HEAD
`54f704a8a92048c5a6a6faa0dd3f3fb34c95f9d8`. The pre-MCP tree contained 243 versioned files and
the expected legitimate uncommitted checkpoint. Ruff format, Ruff lint, mypy, and all 316 baseline
tests passed. The two checkpoint integration workflows rebuilt their governed outputs exactly.

## Artifact classification and retention

| Class | Retained artifacts | Reason |
| --- | --- | --- |
| Contracts | strict single-review models, finalization, corpus-migration and evaluation code plus tests | Required to validate and reproduce the records |
| Human/research inputs | candidate JSONL, governance, explicit decision JSONL, accepted-only dataset | Distinguishes agent proposals from real single-human decisions |
| Decisions | preregistrations, annotation guidelines, workflow records, ADRs and roadmap decisions | Fixes what was decided before outcomes and preserves limitations |
| Reports | validation, conservative baseline, corpus freeze, migration, projection and BM25 diagnostic JSON | Machine-readable derived evidence |
| Source evidence | exact 6.1.0 and 6.2.0 fixtures and strict manifests | Reconstructs normalized corpora and proves raw-byte/release provenance |
| Historical evidence | Phase 4 dataset/report and the exact 6.2.0 mechanical projection | Explains migration equivalence without claiming new human judgment |

No checkpoint artifact was deleted. None is obsolete merely because it is outside the product
runtime. Ignored Python bytecode caches are regenerable but were not material to the Git tree and
did not require a cleanup operation.

## Verified identities

| Artifact | SHA-256 |
| --- | --- |
| Single-review governance | `a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264` |
| Agent candidate batch | `832075827b782c26b4975635f19b836439a2a0d582e36fa59704ee19bbb15abb` |
| Human decisions | `3bb0aa56adb8fc664c65020ee64c54f5b1aecf30d918b24ceeec75323556da2e` |
| Accepted single-review dataset | `bf9c9b515fe0b886db88199b94a2b24f1a60ad60273bd7e266f6d0f757ceab15` |
| Single-review validation report bytes | `fa141ee15a2b0896af3340cf3494b4a0d73a1509a6c4bc69b584b294da8296b8` |
| Conservative baseline report bytes | `06e287491171a116cf18c4b899e8b90272596170e218ef86ed21aedf1d7359bb` |
| PyMC 6.2.0 freeze report bytes | `f3a71f3f332920e78970dcd556353b42feff75a843bc3d4492a843dee5b17a2a` |
| PyMC 6.2.0 provenance corpus identity | `796e7aee3f1fae1423bc04f0478381e6f7338afdd85d2f3a9d1d9cfa692c573a` |
| 6.1.0 to 6.2.0 migration report bytes | `9ce30bd317e7d41bf73086913321a4f42c362075544d0a75f7e075e93d9b6dc4` |
| Projected retrieval dataset bytes | `a681d557e9e93895d95832864071eb6ed94e1f75cb99a74fc93aae495c8eb8e9` |
| Projection report bytes | `3a9e599db3c3cca0e3c63c9dfd5f5f3ff13f69a06db7555867b264dec45d8a19` |
| PyMC 6.2.0 BM25 migration report bytes | `7399ea5bc3f6a4f991131261b0154fe87efa8b327a55c4e0b58426eb889b195d` |

The four 6.2.0 fixture hashes match their manifests. The v2 freeze reconstructs from the checked-in
inputs and binds four normalized documents, 15 chunks, release `v6.2.0`, upstream commit
`3b661c7e5e3ca7d5d7550eca36991d7c1e72274e`, source manifests, and raw hashes. All four raw files
differ from 6.1.0, while all normalized documents and chunks match exactly.

## Reproducible boundary

`test_phase5_single_review_workflow.py` rebuilds the validation and conservative baseline from the
candidate, decision, dataset, and 6.1.0 corpus inputs and compares exact report bytes.
`test_pymc_620_migration.py` rebuilds both corpora and checks the v2 freeze, normalized migration,
mechanical query projection, and every non-latency BM25 result.

The pre-MCP lock identity was
`dcd7f4035ec6e764de84d6b9fbb96e4d27590f146af492169db4d8c3ed7a9da0`. It legitimately pins PyMC
6.2.0 and PyTensor 3.2.2; removed transitive packages are explained by PyTensor's changed dependency
graph. Only after this checkpoint was reproduced separately, the MCP work added the exact official
SDK pin `mcp==2.0.0` and its transitive lock entries. No scientific dependency was upgraded as a
side effect.

## Remaining limitations

- The 24 examples have one human reviewer and no independent adjudication.
- They are exploratory development evidence, not held out or production grade.
- Exact chunk-support coverage is not semantic answer validation.
- The 6.2.0 projection is mechanical and creates no new human labels.
- The active corpus still contains only four official PyMC pages.
- `ConservativeAbstentionPolicy` still authorizes zero answers and no threshold is selected.
