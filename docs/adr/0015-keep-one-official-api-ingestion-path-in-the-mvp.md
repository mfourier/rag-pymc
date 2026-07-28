# ADR-0015: Keep one official API ingestion path in the MVP

- Status: Accepted
- Date: 2026-07-27

## Context

The repository implemented three independent PyMC source pipelines: generated API HTML,
repository Python code, and conceptual Jupyter notebooks. Each additional format required its own
parser, chunker, CLI command, fixtures, tests, provenance rules, and evaluation dataset. Only the
four-page API corpus was adopted by context construction and Phase 5 evidence work.

The repository-code slice was measured on seven answerable development questions. It achieved
Recall@3 `0.714286`, MRR `0.476190`, and nDCG@3 `0.537409`; its report explicitly did not measure a
mixed-corpus documentation regression. The notebook slice achieved perfect retrieval on eight
answerable questions, but the ten-query dataset was hand-curated for three selected notebooks, was
not held out, produced zero correct abstentions on its two unanswerable questions, and also lacked
a mixed-corpus regression experiment.

These slices proved that the formats could be normalized, but neither result established that
maintaining three active ingestion stacks improved the expert-assistant MVP. The next evidence
priority is broader official API coverage and a governed scientific-literature slice, not more
format-specific code without an adopted runtime use case.

## Decision

Keep generated Sphinx API HTML as the only active ingestion path. Remove repository-code and
notebook parsers, chunkers, product CLI commands, optional notebook dependencies, examples, and
feature-specific tests from the installed project. Remove the one-off repository snapshot script
as well; the exact controlled outputs it produced remain versioned.

Retain the exact raw fixtures, source manifests, evaluation datasets, machine-readable reports,
evaluation narratives, and earlier ADRs as historical research evidence. Retain archived source
type identities where research-data validation needs to read those frozen records; they do not
imply an active ingestion capability.

A new source format may return only when it has:

1. a concrete expert-assistant question class that the active corpus cannot support;
2. controlled acquisition, provenance, licensing, and version policy;
3. an independently reviewed development or held-out dataset;
4. a measured regression test against the existing official-source corpus; and
5. an adopted retrieval-to-answer path that justifies its maintenance cost.

## Alternatives considered

### Keep all parsers because they already existed

Rejected because implemented code is still permanent public surface, dependency weight, and test
cost. Historical source and results are sufficient to recreate an experiment if a new adoption
case appears.

### Merge all source types into the default corpus

Rejected because source layers have different authority and neither experiment measured mixed-
corpus ranking or context regressions. Combining them would broaden claims beyond the evidence.

### Delete every experimental artifact

Rejected because the results explain the scope decision and prevent repeating exploratory work
without a stronger hypothesis.

## Consequences

- The installed project has one acquisition-to-chunking path and one documented corpus build.
- Jupyter is no longer a development dependency. The small HDF5 backend remains because the
  independent ArviZ inference-audit utility has a concrete NetCDF contract.
- The Python package is smaller, while exact experimental evidence remains auditable.
- Archived manifests cannot be ingested through the product CLI in the current version.
- Scientific papers must enter through the separate policy and adoption gate rather than by
  reviving an unrelated notebook parser.
