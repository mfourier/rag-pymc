# ADR-0012: Normalize versioned notebook inputs without execution outputs

- Status: Accepted
- Date: 2026-07-24

## Context

Conceptual PyMC documentation is authored as Jupyter notebooks that interleave explanatory
Markdown and executable code. The raw files can also contain megabytes of plots, captured
streams, execution counters, kernel metadata, and environment watermarks. Those artifacts can
reflect a runtime different from the source release and are not required to retrieve the
authored narrative.

The local documentation tree under `datasets/raw/source` has no adjacent whole-tree manifest.
It is useful for discovery but cannot be described as a controlled PyMC 6.1.0 snapshot. The
local upstream clone contains the exact `v6.1.0` Git objects at commit
`56384e5afed6d1ad122e19b1bf3a7885fc38e5e5`.

The six initially considered notebooks total approximately 7.4 MB in raw form, while their
Markdown and code inputs total approximately 98 KB. Three notebooks account for most embedded
output size. Copying every notebook before evaluating retrieval value would conflict with the
incremental source-acquisition policy in ADR-0002.

## Decision

Add a separate `notebook` evidence layer with a first slice containing:

- `dimensionality.ipynb`;
- `pymc_pytensor.ipynb`;
- `model_comparison.ipynb`.

Acquire and hash each complete upstream notebook from the exact Git tag. Keep raw inputs in
controlled fixtures even though the parser ignores some fields; this preserves byte-level
auditability.

Normalize only nonempty Markdown and code input cells. Exclude:

- outputs;
- execution counts;
- cell and notebook metadata;
- kernel specifications;
- raw cells.

Preserve one-based cell numbers, cell type, heading hierarchy, source path, and authored cell
content. Derive PyMC API-symbol metadata conservatively from `pm.<name>` and `pymc.<name>` code
references, excluding underscore-prefixed attributes.

Chunk adjacent cells only when they belong to the same heading section and fit the target
character budget. Never split an individual cell. Record the parser and chunker versions on
processed artifacts.

Keep notebook retrieval experimental. Evaluate it independently and do not merge it into the
default Phase 4 context until a mixed-corpus regression and evidence-sufficiency policy are
available.

Defer the output-heavy `pymc_overview.ipynb`, `posterior_predictive.ipynb`, and
`GLM_linear.ipynb` files until a large-artifact policy or artifact store is selected.

## Alternatives considered

### Ingest the uncontrolled raw documentation tree

Rejected because its complete release, commit, acquisition event, and tree hash are not
recorded.

### Store only normalized notebooks

Rejected because a normalized file is a derived artifact and cannot prove the exact upstream
bytes that were acquired without an additional raw-artifact hash contract.

### Include notebook outputs as retrieval evidence

Rejected because outputs are large, often redundant, and can represent a runtime different
from the authored source release. Output-specific questions require a separate evidence policy.

### Ingest all six notebooks immediately

Rejected because three files contribute several megabytes of embedded outputs before their
incremental retrieval value has been measured.

### Convert notebooks to undifferentiated plain text

Rejected because cell identity, code boundaries, and heading structure are useful for retrieval,
citations, and debugging.

## Consequences

- The authored conceptual narrative is reproducible and protected from stale execution output.
- Notebook-only output claims are deliberately unavailable.
- The first slice produces three documents and 34 deterministic chunks.
- A changed output with unchanged inputs produces the same normalized document and chunks, while
  the raw manifest hash still detects the upstream-byte change.
- Large individual cells can exceed the target chunk size because semantic integrity takes
  precedence over hard truncation.
- High answerable-query recall does not imply semantic abstention; out-of-corpus notebook
  questions still require an evidence-sufficiency policy.
