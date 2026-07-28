# Scientific literature evidence policy

## Purpose

Scientific literature will extend `rag-pymc` beyond library lookup so the assistant can reason
about Bayesian methods, assumptions, diagnostics, validation, and research workflows. This layer
is planned but not yet implemented. The current default corpus still contains only controlled PyMC
6.1.0 API evidence.

The literature layer must improve technical depth without weakening version correctness. It is a
research-authority corpus, not a substitute for official PyMC, ArviZ, or PyTensor evidence.

## Authority boundary

| Claim type | Preferred authority | Paper role |
| --- | --- | --- |
| PyMC signature, parameter, return value, warning, or version compatibility | Pinned official documentation and verified runtime | None unless discussing history or motivation |
| Internal dispatch, validation, graph mutation, or implementation detail | Exact versioned repository source, optionally corroborated by tests | Explain the method, not the installed behavior |
| Statistical assumption, theorem, diagnostic, or validation method | Primary paper plus appropriate methodological references | Primary evidence |
| Empirical performance or comparison | Exact paper, dataset, estimand, and experimental conditions | Primary but conditional evidence |
| Practical modeling recommendation | Official guidance, papers, and explicit project inference | Supporting evidence; recommendation must be labeled |

When sources conflict, the answer must expose the conflict and its scope. Library evidence wins only
for what the pinned software documents or implements. It does not make a statistical method valid.
Paper evidence wins only for the scientific claims it actually studies. It does not make code
compatible with the installed runtime.

## Minimum paper identity

Every admitted paper must record:

- title and authors;
- DOI, arXiv identifier, or another stable identifier when available;
- venue and publication status, distinguishing peer-reviewed versions from preprints;
- publication date and exact version or revision date;
- canonical source URL and acquisition timestamp;
- license or a documented storage and quotation boundary;
- raw content SHA-256 and extraction version;
- retraction, correction, or supersession status when known;
- page, section, figure, table, or equation anchors sufficient for inspectable citations.

Metadata alone is not evidence for a scientific claim. The normalized content and citation anchor
must resolve to the exact acquired artifact.

## Selection policy

Start with a small, question-driven slice. Admit a paper only when it supports a predefined family
of user tasks and there is an evaluation plan for that family. Prefer primary methodological papers,
authoritative corrections, and papers that expose assumptions and failure modes. Reviews can route
queries and establish vocabulary but should not silently replace primary evidence for contested or
precise claims.

“Recent” and “state of the art” are dated claims. A frozen corpus may report what was current at its
declared cutoff. Claiming current state of the art requires an explicit refresh or live verification
step with recorded search date, selection criteria, and source provenance.

Do not bulk-ingest papers merely because they mention Bayesian inference or PyMC. Exclude sources
whose license, identity, version, or relationship to supported questions is unclear.

## Retrieval and context rules

- Store scientific literature separately from API, notebook, repository-code, and test evidence.
- Route by claim need: library behavior, implementation, statistical method, empirical result, or
  project recommendation.
- Preserve evidence-layer identity through retrieval, context construction, generation, and
  citation.
- Do not let a high paper-retrieval score authorize an API claim.
- Require mixed-authority compatibility checks before one context combines library and paper
  evidence.
- Prefer section- or page-sized semantic chunks that retain definitions, conditions, and caveats;
  do not detach a result from its assumptions or experimental setting.
- Treat equations, figures, tables, appendices, and supplementary material as distinct parsing and
  citation concerns rather than flattening them silently into prose.

## Response rules

A grounded response must distinguish:

1. documented library behavior;
2. observed implementation behavior;
3. statistical interpretation;
4. claims reported by research literature; and
5. the assistant's own practical recommendation or inference.

The response must state material assumptions, applicable versions, and important limitations. It
must abstain or narrow the answer when the corpus cannot support a necessary claim. Citation
presence alone is insufficient: later evaluation must assess semantic support and whether caveats
or contradictory evidence were omitted.

## Adoption gate

Before papers enter default context, complete a working vertical slice with:

1. an ADR for acquisition, licensing, normalization, chunking, and update cadence;
2. a controlled manifest and hash-verified raw snapshot;
3. deterministic parsing with inspectable citation anchors;
4. a dedicated development dataset containing answerable, unsupported, conflicting-source, and
   library-versus-literature boundary questions;
5. retrieval and context-budget measurements by evidence layer;
6. semantic citation-support evaluation;
7. a mixed-corpus regression against the frozen library-only baseline; and
8. an explicit decision about freshness checks for claims such as “latest” or “state of the art.”

Until this gate passes, local skill references and papers may guide deliberate analysis workflows,
but the runtime RAG must not claim that it retrieves or grounds answers in a production scientific
literature corpus.
