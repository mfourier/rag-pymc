# rag-pymc

`rag-pymc` is an evidence-grounded adaptive tutor for learning probabilistic programming
with PyMC. The project is designed as an Applied Science system: retrieval quality,
version correctness, pedagogical behavior, and reproducibility are first-class concerns.

The repository has completed **Phase 4: hybrid retrieval and reranking**. It can ingest four
controlled PyMC 6.1.0 API pages, search 15 structure-aware chunks with BM25, exact dense
retrieval, weighted Reciprocal Rank Fusion, or cross-encoder reranking, and compare all methods
on a versioned 30-query dataset. Equal-weight RRF remains the selected ranking policy because
the measured cross-encoder reduces quality and adds substantial CPU latency. The implemented
Phase 5 foundations convert ranked chunks into deterministic, budget-bounded context, expose
that artifact for local CLI inspection, add a conservative evidence-assessment boundary,
define provider-neutral grounded-answer contracts, and measure structural response validity
and citation traceability deterministically. The current policy always abstains and never
claims that evidence is sufficient. Answer-permitting calibration, semantic response
evaluation, generation, and a Phase 5 dataset are not yet implemented.

Context v1 admits candidates from only one normalized library; a compatibility policy must
exist before PyMC, ArviZ, and PyTensor evidence can share one context. The structured
`ContextItem` and `ConstructedContext` JSON fields are authoritative. `rendered_text` is a
derived accounting and inspection representation, not a prompt or trusted generator framing.
Prompt-safe framing and escaping remain deferred to the provider and prompt-versioning ADR
required before generation.

## Design principles

- Keep domain models independent from orchestration frameworks and external providers.
- Preserve source provenance and library versions from ingestion through citation.
- Establish measurable retrieval baselines before adding generation or tuning learned rankers.
- Treat evaluation datasets, seeds, configurations, and per-query results as versioned
  research artifacts.
- Grow the package around working vertical slices instead of creating empty modules.

Architecture decisions are documented in the [architecture overview](docs/architecture/overview.md),
[ADR-0001](docs/adr/0001-keep-the-core-independent-from-langchain.md),
[ADR-0002](docs/adr/0002-version-source-snapshots-and-content-addressed-artifacts.md),
[ADR-0003](docs/adr/0003-use-jsonl-for-the-local-corpus-baseline.md),
[ADR-0004](docs/adr/0004-use-explicit-bm25-and-versioned-evaluation-artifacts.md),
[ADR-0005](docs/adr/0005-use-pinned-bge-and-exact-cosine-for-the-dense-baseline.md),
[ADR-0006](docs/adr/0006-use-weighted-rrf-before-cross-encoder-reranking.md),
[ADR-0007](docs/adr/0007-evaluate-pinned-ms-marco-cross-encoder-without-adopting-it.md),
[ADR-0008](docs/adr/0008-define-deterministic-context-construction.md), and
[ADR-0009](docs/adr/0009-fail-closed-with-a-conservative-no-threshold-evidence-policy.md).
Measured behavior is documented in the
[Phase 2 sparse](docs/evaluation/phase2-sparse-baseline.md),
[Phase 3 dense](docs/evaluation/phase3-dense-baseline.md), and
[Phase 4 hybrid](docs/evaluation/phase4-hybrid-baseline.md) reports.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) 0.11.29 or newer recommended
- Git, for installing the pre-commit hooks

The scientific compatibility baseline was checked on 2026-07-19 against the published
releases of [PyMC 6.1.0](https://pypi.org/project/pymc/6.1.0/),
[ArviZ 1.2.0](https://pypi.org/project/arviz/1.2.0/), and
[PyTensor 3.1.3](https://pypi.org/project/pytensor/3.1.3/). Exact resolved transitive
versions are recorded in `uv.lock`.

## Install

```bash
uv sync --all-groups
uv run pre-commit install
uv run rag-pymc doctor
```

`uv sync` creates or updates `.venv` from `pyproject.toml` and `uv.lock`. No separate
`requirements.txt` is maintained; this avoids two competing dependency specifications.
PyTorch is resolved from its official CPU-only package index. Embedding and reranking model
weights are not stored in Git: an explicit `--allow-download` on the first corresponding
command caches each exact revision outside the repository, while later commands default to
local files only.

## Ingest the controlled sources

The checked-in fixtures are hash-verified snapshots of four official PyMC 6.1.0 API pages.
All ingestion commands are offline.

Build the original one-page corpus used by Phases 2 and 3:

```bash
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.sample.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.sample.html \
  --output-dir datasets/processed/local
```

Build the expanded Phase 4 corpus:

```bash
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.sample.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.sample.html \
  --output-dir datasets/processed/phase4
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.Data.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.Data.html \
  --output-dir datasets/processed/phase4
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.model.core.set_data.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.model.core.set_data.html \
  --output-dir datasets/processed/phase4
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.sample_posterior_predictive.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.sample_posterior_predictive.html \
  --output-dir datasets/processed/phase4
```

A successful Phase 4 build writes four documents and 15 deterministic chunks. Repeating the
commands upserts the same records. Local processed output is ignored by Git; source fixtures
and manifests are tracked.

## Search the local corpus with BM25

```bash
uv run rag-pymc search "How do I pass target_accept to NUTS?" \
  --corpus-dir datasets/processed/local \
  --library pymc \
  --library-version 6.1.0 \
  --top-k 3
```

Each result includes its score, chunk ID, section, exact library version, and source URL.

## Search the local corpus with dense retrieval

```bash
# First run only, when the pinned model revision is not cached:
uv run rag-pymc search-dense "How do I pass target_accept to NUTS?" --allow-download

# Reproducible offline run after the model is cached:
uv run rag-pymc search-dense "How do I pass target_accept to NUTS?" \
  --corpus-dir datasets/processed/local \
  --library pymc --library-version 6.1.0 --top-k 3
```

## Search the expanded corpus with hybrid retrieval

```bash
uv run rag-pymc search-hybrid "How do I update predictors for prediction?" \
  --corpus-dir datasets/processed/phase4 \
  --library pymc --library-version 6.1.0 --top-k 3
```

The command fuses ten BM25 and ten dense candidates with equal-weight RRF, then returns the
top three. Use `--allow-download` only when the pinned embedding revision is not cached.

## Inspect deterministic grounded context

```bash
uv run rag-pymc inspect-context \
  "How do I update predictors for prediction?" \
  --token-budget 2048
```

`inspect-context` runs the selected Phase 4 retrieval policy over
`datasets/processed/phase4`: BM25 (`k1=1.5`, `b=0.75`) and exact cosine retrieval with the
pinned BGE model feed equal-weight RRF with ten candidates per component, `rrf_k=60`, and a
default final depth of three. The final depth can be set from one through ten with `--top-k`.
The command defaults to PyMC 6.1.0, accepts repeated `--source-type` and `--api-symbol`
filters, and keeps the model manifest, CPU device, batch size, and seed fixed internally.

`--token-budget` is required and uses the deterministic `technical-v1` accounting policy.
The count includes each admitted item's provenance metadata and complete content; it is not
an LLM token count. Standard output contains only the indented `ConstructedContext` JSON, so
fixed inputs and a locally cached model produce the same inspectable artifact. Model loading
defaults to local files only; use `--allow-download` solely for explicit first acquisition.

An empty context is a valid JSON result when retrieval returns no candidates or the first
ranked item exceeds the budget. It does not itself implement an evidence-sufficiency or
abstention decision. The command does not generate an answer and does not persist the
artifact.

## Assess evidence conservatively

`EvidenceAssessment` records a versioned sufficiency value, an explicit abstention decision,
deterministic reason codes, and the exact included and omitted chunk IDs. The
`ConservativeAbstentionPolicy` is identified as `conservative-no-threshold-v1` and behaves as
follows:

- no retrieved evidence is `insufficient`;
- evidence entirely excluded by the context budget is `insufficient` with a distinct reason;
- every nonempty context is `not_assessed`, with budget omission recorded when present;
- every outcome abstains, and this policy never returns `sufficient`.

This zero-answer-coverage behavior is an intentional fail-closed boundary, not a measured
abstention-quality result. It uses no retrieval score, confidence, or threshold. A future
answer-permitting policy requires a separately authored development dataset, a richer
versioned evidence-signal contract, predefined calibration metrics, and an untouched Phase 5
evaluation set. The final Phase 4 dataset remains unavailable for threshold tuning.

## Define and evaluate grounded response structures

Immutable provider-neutral contracts now represent `Citation`, `AtomicClaim`,
`GroundedAnswerSection`, `GroundedAnswer`, `GeneratorInput`, and `GeneratorOutput`.
Non-abstaining answers contain ordered atomic claims, their declared citations, and
organizational headings; headings are metadata and must not be treated as factual answer
content. Abstaining answers contain neither claims nor citations. `GeneratorInput` binds the
exact query, context, and assessment and requires an explicitly sufficient, non-abstaining
decision. `GeneratorOutput` then resolves every citation to an included context item and
requires exact chunk, document, URL, library/version, section, and API-symbol provenance.
Uncited claims remain representable so citation completeness can later be measured instead
of being enforced away.

The pure `evaluate_structural_response` function implements the versioned
`structural-citation-v1` evaluator. It strictly parses one raw JSON answer, validates the
answer and output contracts in stages, records sanitized failures, and reports citation
resolution and provenance diagnostics without retaining claim text, headings, query text, or
context content. It does retain caller- and provider-controlled identifiers plus linkable
hashes, so reports remain potentially sensitive and identifiers must not contain prose or
secrets. `aggregate_structural_responses` canonically orders unique response IDs, embeds the
exact revalidated records, and computes a deterministic structural funnel plus micro citation
and reference rates. Undefined zero-denominator rates remain `null`.

These checks establish syntax, contract validity, and structural traceability only. They do
not establish answer correctness, semantic citation correctness, citation completeness, or
evidence-policy quality. The conservative production policy cannot construct a
`GeneratorInput`; tests use an explicit sufficient fixture solely to exercise the positive
contract boundary. There is still no generator protocol, fake or provider implementation,
generation orchestration, response-evaluation CLI, or automatic report persistence.

## Search with the experimental reranker

```bash
uv run rag-pymc search-reranked "Where are prediction samples stored?" \
  --corpus-dir datasets/processed/phase4 \
  --library pymc --library-version 6.1.0 --top-k 3
```

This command reranks the frozen RRF top ten with the pinned MS MARCO cross-encoder. It is
available for experimentation but is not the selected default policy.

## Reproduce the sparse baseline

```bash
uv run rag-pymc evaluate \
  --dataset datasets/evaluation/phase2/pymc_sample_queries.jsonl \
  --corpus-dir datasets/processed/local \
  --output reports/evaluation/phase2-bm25-baseline.json \
  --top-k 3 \
  --seed 20260719 \
  --k1 1.5 \
  --b 0.75
```

The first run achieved Recall@3 1.000000, MRR 0.842593, nDCG@3 0.882933, and correct
abstention 0.000000. These values validate this narrow pipeline only; the corpus contains one
page and five chunks. The report preserves all rankings and limitations.

## Reproduce the dense baseline and comparison

```bash
uv run rag-pymc evaluate-dense
```

The command writes `reports/evaluation/phase3-dense-baseline.json` and
`reports/evaluation/phase3-sparse-vs-dense.json`.

At `k=3`, dense retrieval achieved Recall 0.944444, MRR 0.814815, and nDCG 0.847881.
The freshly executed BM25 control achieved Recall 1.000000, MRR 0.842593, and nDCG 0.882933.
Dense improved the first relevant rank for three queries, BM25 did better for two, and 15
tied. Both methods had correct abstention 0.000000 because no threshold policy exists.

The BGE model truncates inputs beyond 512 word pieces. Two of the five current chunks exceed
that limit, and the only answerable dense miss targets evidence late in the Parameters chunk.
The report records this limitation; it does not establish truncation as the cause.

## Reproduce the Phase 4 hybrid baseline

```bash
uv run rag-pymc evaluate-hybrid
```

The command executes fresh BM25, dense, and equal-weight RRF arms on the same 30-query
dataset and writes five JSON artifacts under `reports/evaluation/`. Use
`--allow-download` only for the first model acquisition.

At `k=3`, hybrid retrieval achieved Recall 0.925926, MRR 0.783951, and nDCG 0.820543.
The expanded-corpus BM25 control achieved Recall 0.925926, MRR 0.771605, and nDCG 0.811723;
dense achieved Recall 0.814815, MRR 0.685185, and nDCG 0.718251. Hybrid therefore improves
ordering over BM25 without improving its Recall, while adding 9.316400 ms of mean query
latency in this run.

Correct abstention is 0.666667 for all arms because metadata filters exclude two
out-of-library questions, while one in-library but unsupported question still retrieves PyMC
chunks. See the Phase 4 report for category slices, per-query failures, hashes, and limitations.

## Reproduce the Phase 4 reranking experiment

```bash
uv run rag-pymc evaluate-reranked
```

The command writes a fresh RRF control, the reranked report, and their comparison. The
cross-encoder achieved Recall@3 0.888889, MRR 0.777778, and nDCG@3 0.806873, compared with
0.925926, 0.783951, and 0.820543 for the RRF control. Mean query latency increased from
9.661346 ms to 287.972640 ms.

The reranker recovered the documented Beta-Binomial example but lost two answers previously
inside the RRF top three. It is therefore not adopted. The report preserves all changes by
query and intent without post-hoc threshold tuning.

## Development commands

```bash
uv run ruff format .
uv run ruff check .
uv run mypy
uv run pytest
uv run pre-commit run --all-files
```

The non-mutating validation sequence is:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run rag-pymc doctor
```

## Current structure

```text
datasets/
|-- evaluation/{phase2,phase4}/     # Versioned questions and binary qrels
|-- fixtures/pymc/6.1.0/            # Controlled offline HTML snapshots
`-- raw/manifests/                  # Source, embedding, and reranker provenance
reports/evaluation/                  # Machine-readable experiment results
src/rag_pymc/
|-- abstention/                      # Conservative evidence assessment boundary
|-- application/                     # Retrieval-to-context inspection use case
|-- domain/                          # Source, context, assessment, and answer contracts
|-- context/                         # Deterministic context construction
|-- embeddings/                      # Pinned dense embedding adapter
|-- ingestion/                       # Integrity checks and orchestration
|-- parsing/                         # Sphinx API parser
|-- chunking/                        # Structure-aware API chunker
|-- persistence/                     # Deterministic JSONL corpus adapter
|-- indexing/                        # Explicit BM25 and exact cosine indexes
|-- retrieval/                       # Sparse, dense, and RRF retrieval
|-- reranking/                       # Provider-neutral cross-encoder boundary
|-- evaluation/                      # Retrieval and structural-response evaluation
`-- cli.py                           # Reproducible workflows and JSON context inspection
tests/
|-- unit/
`-- integration/
docs/
|-- adr/
|-- architecture/
`-- evaluation/
```

## Near-term roadmap

- **Phase 5:** define the development-data annotation and deterministic JSONL-loading
  contracts, then add gold-backed evaluators before authoring and hashing development data.
  Add a deterministic generator fake and orchestration only after those evaluation gates.
- Define cross-library compatibility before admitting evidence from multiple normalized
  libraries into one context.
- Create a separate Phase 5 development dataset before calibrating any evidence signal or
  selecting an abstention threshold; keep the Phase 4 final set frozen.
- Evaluate truncation-aware parent-child chunking separately from rank fusion.

LLM generation, PostgreSQL, vector databases, code execution, web APIs, and user interfaces
remain outside the current scope.
