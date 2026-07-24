# rag-pymc

`rag-pymc` is an evidence-grounded adaptive tutor for learning probabilistic programming
with PyMC. The project is designed as an Applied Science system: retrieval quality,
version correctness, pedagogical behavior, and reproducibility are first-class concerns.

An experimental repository-code ingestion slice now complements the frozen Phase 4 API
baseline. It snapshots four exact PyMC 6.1.0 implementation files, selects public symbols with
the Python AST, and keeps this evidence in a separate corpus until retrieval regressions are
measured.

An additional conceptual-notebook slice snapshots three exact PyMC 6.1.0 notebooks and indexes
only their Markdown and code inputs. Execution outputs and environment metadata are excluded
from normalized retrieval content. This corpus also remains opt-in.

The repository has completed **Phase 4: hybrid retrieval and reranking**. It can ingest four
controlled PyMC 6.1.0 API pages, search 15 structure-aware chunks with BM25, exact dense
retrieval, weighted Reciprocal Rank Fusion, or cross-encoder reranking, and compare all methods
on a versioned 30-query dataset. Equal-weight RRF remains the selected ranking policy because
the measured cross-encoder reduces quality and adds substantial CPU latency. The implemented
Phase 5 foundations convert ranked chunks into deterministic, budget-bounded context, expose
that artifact for local CLI inspection, add a conservative evidence-assessment boundary,
define provider-neutral grounded-answer contracts, and measure structural response validity
and citation traceability deterministically. Phase 5 development annotations now have strict
immutable contracts, deterministic JSONL loading, and a gold-evidence evaluator that separates
retrieval coverage from budget loss and scores abstention decisions with fixed denominators.
The current policy always abstains and never claims that evidence is sufficient. A
human-authored Phase 5 dataset, answer-permitting calibration, semantic response evaluation,
and generation are not yet implemented.

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
[ADR-0008](docs/adr/0008-define-deterministic-context-construction.md),
[ADR-0009](docs/adr/0009-fail-closed-with-a-conservative-no-threshold-evidence-policy.md),
[ADR-0010](docs/adr/0010-separate-versioned-repository-code-from-documentation.md), and
[ADR-0011](docs/adr/0011-evaluate-gold-evidence-before-calibrating-abstention.md), and
[ADR-0012](docs/adr/0012-normalize-versioned-notebook-inputs-without-execution-outputs.md).
Measured behavior is documented in the
[Phase 2 sparse](docs/evaluation/phase2-sparse-baseline.md),
[Phase 3 dense](docs/evaluation/phase3-dense-baseline.md), and
[Phase 4 hybrid](docs/evaluation/phase4-hybrid-baseline.md) reports. The opt-in source-code
slice has a separate
[repository-code BM25 development baseline](docs/evaluation/repository-code-bm25-baseline.md),
and the conceptual slice has a
[notebook BM25 development baseline](docs/evaluation/notebook-bm25-development.md).

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

## Ingest the experimental PyMC implementation corpus

The repository-code slice mirrors the same four public symbols as Phase 4 and is pinned to
PyMC tag `v6.1.0` at commit `56384e5afed6d1ad122e19b1bf3a7885fc38e5e5`.

```bash
uv run python scripts/snapshot_pymc_repository.py \
  --repository /home/mlioi/pymc \
  --project-root /home/mlioi/rag-pymc

for symbol in pymc.sample pymc.Data pymc.model.core.set_data pymc.sample_posterior_predictive
do
  case "$symbol" in
    pymc.sample) source=pymc/sampling/mcmc.py ;;
    pymc.Data) source=pymc/data.py ;;
    pymc.model.core.set_data) source=pymc/model/core.py ;;
    pymc.sample_posterior_predictive) source=pymc/sampling/forward.py ;;
  esac
  uv run rag-pymc ingest-code \
    --manifest "datasets/raw/manifests/pymc/6.1.0/repository/$symbol.json" \
    --source "datasets/fixtures/pymc/6.1.0/repository/$source" \
    --output-dir datasets/processed/repository-code
done
```

This produces four documents and 19 deterministic AST chunks. It does not change the Phase 4
corpus or the default context policy. See
[`docs/corpus/pymc-source-selection.md`](docs/corpus/pymc-source-selection.md) for the source
selection, exclusions, query routing, and adoption gate.

## Ingest the experimental conceptual notebooks

```bash
uv run rag-pymc ingest-notebook \
  --manifest datasets/raw/manifests/pymc/6.1.0/notebooks/dimensionality.json \
  --source datasets/fixtures/pymc/6.1.0/notebooks/docs/source/learn/core_notebooks/dimensionality.ipynb \
  --output-dir datasets/processed/notebooks

uv run rag-pymc ingest-notebook \
  --manifest datasets/raw/manifests/pymc/6.1.0/notebooks/pymc_pytensor.json \
  --source datasets/fixtures/pymc/6.1.0/notebooks/docs/source/learn/core_notebooks/pymc_pytensor.ipynb \
  --output-dir datasets/processed/notebooks

uv run rag-pymc ingest-notebook \
  --manifest datasets/raw/manifests/pymc/6.1.0/notebooks/model_comparison.json \
  --source datasets/fixtures/pymc/6.1.0/notebooks/docs/source/learn/core_notebooks/model_comparison.ipynb \
  --output-dir datasets/processed/notebooks
```

The result is three documents and 34 deterministic chunks. Outputs and notebook metadata remain
in the hash-verified raw fixtures but are deliberately absent from normalized documents.

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

## Freeze the first Phase 5 annotation corpus

Before authoring Phase 5 examples, freeze the exact processed annotation corpus with
`rag-pymc freeze-annotation-corpus`. The command requires an explicit stable annotation
namespace, logical project-relative corpus path, library/version boundary, admitted source
types, limitations, and output path. It validates document/chunk parentage and transformation
versions, fails on undeclared evidence layers, and writes a deterministic
`phase5-annotation-corpus-freeze-v1` record.

The first Gate A artifact freezes only the four selected PyMC 6.1.0 API pages: four documents,
15 chunks, `sphinx-api-v1`, `api-reference-v1`, and corpus SHA-256
`af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2`. Rebuild instructions,
controlled input hashes, limitations, and the exact command are recorded in the
[Phase 5 annotation corpus freeze](docs/evaluation/phase5-annotation-corpus-freeze-v1.md).
This artifact contains no candidate queries or human judgments; Gate B batch preregistration
must precede annotation.

## Evaluate development evidence against atomic gold support

`Phase5DevelopmentExample` separates corpus answerability from runtime outcomes and records
atomic claims with alternative minimal chunk-support sets. Annotation and adjudication
provenance are mandatory and adjudicators cannot also be annotators for the same example.
`load_phase5_development_dataset` strictly reads JSONL, rejects duplicate JSON keys and
non-finite numbers, preserves file order, hashes exact raw bytes, and requires one corpus
SHA-256 namespace under `canonical-chunk-identity-json-v1`.

`hash_phase5_corpus` computes that order-invariant identity from canonical chunk ID/content
hash records. Before evaluation, `validate_phase5_development_corpus` verifies the declared
hash, rejects duplicate corpus chunk IDs, resolves every gold support reference, and requires
each referenced chunk to match the annotated library and version. The accepted workflow is
documented in the
[Phase 5 annotation guidelines](docs/evaluation/phase5-development-annotation-guidelines-v1.md).

The preflight command emits only the deterministic validation report JSON on standard output:

```bash
uv run rag-pymc validate-development-data \
  --dataset datasets/evaluation/phase5/development.jsonl \
  --corpus-dir datasets/processed/phase5
```

Both paths are required because no development dataset or corpus is silently selected. On a
validation failure, standard output remains empty and a controlled diagnostic is written to
standard error.

The pure `evaluate_gold_evidence` evaluator binds an annotation to an exact corpus, query,
constructed context, and evidence assessment. It measures claim coverage first over admitted
context and then over admitted plus budget-omitted candidates. This distinguishes a retrieval
miss from evidence found by retrieval but lost to the context budget. A query is answerable
from runtime context only when every atomic gold claim has at least one complete support set
in that context.

`aggregate_gold_evidence` requires exactly one result for every development example and one
policy version. It reports answer coverage, selective risk, false-answer rate,
false-abstention rate, decision accuracy, and micro claim coverage with explicit counts and
`null` for undefined conditional rates. The evaluator compares adjudicated chunk identities;
it does not establish semantic correctness, citation quality, or answer usefulness. ADR-0011
fixes these definitions before any human development data or threshold is selected.

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

- **Phase 5:** author and independently adjudicate the first development dataset using the
  frozen annotation, loading, and `phase5-gold-evidence-v1` evaluation contracts; bind it to
  an exact corpus hash and record the conservative-policy baseline before designing any
  answer-permitting signal or threshold. Add a deterministic generator fake and orchestration
  only after those evaluation gates.
- Define cross-library compatibility before admitting evidence from multiple normalized
  libraries into one context.
- Keep the Phase 4 final set frozen and create a separate untouched Phase 5 held-out set only
  after the development policy, loss, threshold rule, and metrics are fixed.
- Evaluate truncation-aware parent-child chunking separately from rank fusion.

LLM generation, PostgreSQL, vector databases, code execution, web APIs, and user interfaces
remain outside the current scope.
