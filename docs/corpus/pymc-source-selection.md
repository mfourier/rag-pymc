# PyMC source selection

## Active source boundary

The MVP ingests only hash-verified generated PyMC API HTML. This format provides resolved
signatures, parameter descriptions, returns, notes, examples, stable sections, public URLs, and
explicit library-version provenance through one exercised parser and chunker.

The active PyMC 6.2.0 slice contains:

| Public symbol | Primary use |
| --- | --- |
| `pymc.sample` | Sampling configuration, step assignment, outputs, and examples |
| `pymc.Data` | Data registration, dimensions, mutability, and model context |
| `pymc.model.core.set_data` | Updating model data for prediction workflows |
| `pymc.sample_posterior_predictive` | Posterior prediction inputs, outputs, and groups |

Exact fixtures live under `datasets/fixtures/pymc/6.2.0/`; manifests live under
`datasets/raw/manifests/pymc/6.2.0/`. A corpus build produces four documents and 15 deterministic
chunks under `source_type=api_reference`. The provenance-complete freeze uses
`canonical-corpus-provenance-json-v2` and binds the source manifests, raw fixture hashes, release
tag, upstream commit, normalized documents, and normalized chunks.

The PyMC [API index](https://www.pymc.io/projects/docs/en/stable/api.html) is a symbol catalog for
choosing future pages. It is not ingested as one evidence document: index entries identify symbols
but do not contain the complete generated signatures, parameter descriptions, notes, and examples.
Each selected generated detail page must receive its own exact fixture and strict manifest before
it can enter the controlled corpus.

## Expansion rule

Expand breadth through the same source format before adding another parser. Select new API pages
from observed user questions and the API index, define evaluation queries first, acquire exact
versioned HTML, record release/commit, license, acquisition time, and SHA-256, then measure
retrieval and context cost.

Likely future API families include model construction, distributions, diagnostics, dimensions,
sampling backends, log probability, posterior prediction, and ArviZ interoperation. Selection must
remain incremental and question-driven rather than crawling the entire documentation site.

## Archived source experiments

The repository contains exact PyMC 6.1.0 snapshots of four implementation files and three
conceptual notebooks. Their parsers, chunkers, CLI commands, and runtime retrieval paths were
removed from the MVP after separate development experiments.

Repository-code BM25 reached Recall@3 `0.714286`; it did not justify default adoption. Notebook
BM25 ranked all eight answerable development questions first but failed both unsupported questions,
and the qrels were authored after inspecting the corpus. These results remain documented in:

- [repository-code BM25 development baseline](../evaluation/repository-code-bm25-baseline.md);
- [notebook BM25 development baseline](../evaluation/notebook-bm25-development.md);
- [ADR-0010](../adr/0010-separate-versioned-repository-code-from-documentation.md); and
- [ADR-0012](../adr/0012-normalize-versioned-notebook-inputs-without-execution-outputs.md).

[ADR-0015](../adr/0015-keep-one-official-api-ingestion-path-in-the-mvp.md) supersedes the two
source-format decisions for the active MVP.

The raw snapshots and manifests remain solely to preserve the experiments. They are not accepted by
the active ingestion command. A future implementation-query or conceptual-source proposal must
define a new held-out dataset and demonstrate benefit against the simpler API-only baseline.

## Authority rules

- Prefer generated API pages for public signatures, parameters, returns, warnings, and supported
  examples.
- Verify version-sensitive code against the pinned runtime when documentation is ambiguous.
- Do not treat archived repository implementation as a public compatibility guarantee.
- Do not treat notebook outputs or environment metadata as source evidence.
- Route statistical methods and research claims to the separate scientific-literature policy.
- Preserve source-layer identity through retrieval, context, generation, and citation.

## Exclusions

The MVP does not ingest:

- the complete PyMC repository;
- upstream tests or CI configuration;
- arbitrary notebooks or their execution outputs;
- generated documentation indexes without resolved content;
- contributor logistics unrelated to supported questions;
- files from a different release under a PyMC 6.2.0 namespace; or
- scientific papers through the API-documentation parser.
