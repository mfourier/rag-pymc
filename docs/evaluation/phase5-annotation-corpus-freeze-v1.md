# Phase 5 annotation corpus freeze v1

## Status and boundary

Gate A is complete for the first Phase 5 development-annotation namespace. The frozen corpus
contains only the selected Phase 4 PyMC API-reference sources. It does not contain candidate
queries, annotations, adjudications, retrieval outcomes, evidence-policy scores, or accepted
development examples.

The annotation namespace is `pymc-6.1.0-api-phase5-development-v1`. Any source, parser,
chunker, or normalized-content change creates a different corpus SHA-256 and requires a new
namespace plus review of every future support set.

## Controlled inputs

All four inputs are PyMC `v6.1.0` at source commit
`56384e5afed6d1ad122e19b1bf3a7885fc38e5e5`, use Apache-2.0 provenance, and are verified
against the exact raw SHA-256 in their checked-in manifests.

| API symbol | Raw fixture SHA-256 |
|---|---|
| `pymc.Data` | `e4ea25f1178592a5b5d475ac7ffd4cddda5f930715734b0ee2948c15273d9402` |
| `pymc.model.core.set_data` | `d123ea93e161192ba8cf00c445f35ef20478e74540110b4c3ec4a49bfb1bc8df` |
| `pymc.sample` | `48ec372999fdfc86bbdbd11aa7ebeb3185a2488a58a055db00f86320dfdc3d35` |
| `pymc.sample_posterior_predictive` | `20d65310024f100b06a880551c160a0a9c0e6df4652621a45692b4212f28a869` |

The checked-in manifests and fixtures are authoritative build inputs. The processed JSONL
directory is deliberately ignored by Git and must be rebuilt before annotation or validation.

## Frozen identity

| Field | Value |
|---|---|
| Logical corpus path | `datasets/processed/phase5-annotation-api-v1` |
| Library and version | `pymc` `6.1.0` |
| Source types | `api_reference` |
| Documents | 4 |
| Chunks | 15 |
| Parser versions | `sphinx-api-v1` |
| Chunker versions | `api-reference-v1` |
| Corpus hash policy | `canonical-chunk-identity-json-v1` |
| Corpus SHA-256 | `af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2` |

The machine-validated record is
`reports/evaluation/phase5-annotation-corpus-freeze-v1.json`. Its corpus SHA-256 is the
order-invariant identity over sorted chunk ID and content-hash records; it is not the byte hash
of `chunks.jsonl`.

## Reproduction

Build the corpus into a new or already matching output directory by running the four controlled
ingestion commands documented in `README.md`. Then create or verify the freeze artifact:

```bash
uv run rag-pymc freeze-annotation-corpus \
  --corpus-dir datasets/processed/phase5-annotation-api-v1 \
  --corpus-path datasets/processed/phase5-annotation-api-v1 \
  --annotation-namespace pymc-6.1.0-api-phase5-development-v1 \
  --library pymc \
  --library-version 6.1.0 \
  --source-type api_reference \
  --limitation "Chunk-identity coverage does not establish semantic support, citation correctness, answer correctness, or usefulness." \
  --limitation "The corpus contains generated API reference pages for only four PyMC public symbols." \
  --limitation "The corpus excludes conceptual notebooks, repository code, ArviZ, and PyTensor sources." \
  --output reports/evaluation/phase5-annotation-corpus-freeze-v1.json
```

The command fails closed on an undeclared library, version, or source layer; missing parser or
chunker versions; missing or inconsistent document parents; empty inputs; or a non-portable
logical corpus path. The integration test rebuilds all four sources and compares the complete
derived report with the checked-in artifact.

## Limitations

- Only four generated API pages are available, so conceptual, diagnostic, mathematical, and
  implementation questions can be corpus-unanswerable even when PyMC supports the topic.
- Notebook and repository-code evidence remain experimental and excluded. ArviZ and PyTensor
  evidence are also absent.
- Chunk-identity coverage cannot establish semantic support, citation correctness, answer
  correctness, or usefulness.
- This freeze is not a development dataset and contains no human judgment.

## Next gate

Gate B must preregister the first development-batch design before candidate JSONL records are
written. It must fix query count, coverage targets, query and template families, answerable and
in-library hard-negative balance, intent and difficulty slices, expected API-symbol coverage,
review roles, held-out leakage prevention, and the limitations of this API-only corpus.
