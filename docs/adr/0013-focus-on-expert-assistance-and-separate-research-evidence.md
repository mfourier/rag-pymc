# ADR-0013: Focus on expert assistance and separate research evidence

- Status: Accepted
- Date: 2026-07-27

## Context

The repository was initially described as an adaptive tutor for learning PyMC. Its implemented
vertical slices do not model a learner, select a curriculum, track progress, generate exercises,
or optimize teaching behavior. They ingest versioned sources, retrieve technical evidence,
construct bounded context, assess evidence conservatively, validate grounded-answer contracts,
and evaluate citation traceability.

The intended user is an engineer, data scientist, or researcher who wants to design, implement,
debug, validate, and communicate Bayesian analyses with PyMC. That user needs an expert assistant
that distinguishes documented library behavior, implementation details, statistical
interpretation, research findings, and practical recommendations. A tutoring product would add
longitudinal user state and a separate set of pedagogical objectives without improving the core
evidence boundary.

Research papers are valuable for statistical methods, diagnostics, model criticism, and modern
workflow recommendations. They have a different authority from official PyMC documentation and
source code. A paper can motivate a method without proving that a particular PyMC release exposes
an API or implements the method in the way required by generated code.

## Decision

Define `rag-pymc` as an evidence-grounded expert assistant for Bayesian statistics and PyMC.
Grounded LLM generation is an intended capability once the existing evidence and evaluation gates
authorize it.

The assistant may adapt retrieval, evidence selection, response organization, and declared
limitations to the technical task. It must not maintain a learner profile, infer mastery, sequence
a curriculum, track progress, generate assessments as part of a teaching plan, or optimize a
pedagogical policy. These are product non-goals rather than deferred features.

Retain `Difficulty` as a technical evaluation stratum. It describes the reasoning or source-reading
burden of a query or chunk; it does not describe a user or authorize personalized behavior.

Keep evidence in explicit authority layers:

1. **Official library documentation and release metadata** support public API, compatibility, and
   documented-behavior claims for a pinned version.
2. **Versioned repository implementation** supports implementation and debugging claims but does
   not replace the public API contract.
3. **Upstream tests** may corroborate asserted edge cases but do not create public guarantees.
4. **Scientific literature** supports statistical methods, assumptions, diagnostics, and reported
   empirical findings. It does not establish library-version compatibility.
5. **Project inference or recommendation** must be labeled as such and must not be presented as a
   quotation or guarantee from an evidence source.

Scientific papers must enter through a separate, versioned corpus with exact provenance,
publication status, stable identifiers, acquisition metadata, content hashes, and section- or
page-resolvable citations. Paper ingestion and mixed-authority retrieval require their own vertical
slice and evaluation before becoming part of default context.

Historical ADRs, preregistrations, and frozen evaluation artifacts may retain tutoring or
pedagogical terminology because rewriting accepted research records would weaken provenance. They
must be interpreted under this ADR for future work. Active package metadata, architecture, source
documentation, and roadmap use the expert-assistant boundary.

## Alternatives considered

### Continue toward an adaptive tutor

Rejected because it would require learner identity, longitudinal state, progress models,
curriculum policies, exercise workflows, and pedagogical evaluation that are independent of the
implemented evidence-grounding core.

### Build a generic Bayesian chatbot

Rejected because generic generation would weaken the project's version correctness, explicit
evidence authority, conservative abstention, and reproducible evaluation advantages.

### Mix papers and library documentation into one undifferentiated corpus

Rejected because retrieval rank would obscure whether a claim describes a statistical method, a
research result, a public API contract, or implementation behavior. It would also make version
compatibility and citation evaluation ambiguous.

### Exclude scientific literature

Rejected because official API documentation cannot fully support questions about methodological
assumptions, calibration, causal identification, diagnostics, study design, or current statistical
practice.

## Consequences

- Most implemented ingestion, retrieval, context, abstention, citation, and evaluation work remains
  directly applicable.
- Grounded response generation and semantic correctness remain required; removing tutoring does not
  remove the need to calibrate when the assistant may answer.
- No user-learning database, mastery model, curriculum engine, pedagogical policy, or associated
  privacy boundary is required.
- Query difficulty remains useful for evaluation without implying personalization.
- Paper ingestion adds provenance, licensing, freshness, authority-routing, and evaluation work, but
  it is isolated from the trusted library-version corpus.
- Claims that a method is recent or state of the art require a dated literature corpus or an
  explicit fresh-source verification step. The assistant must not infer freshness from an old
  snapshot.
- Existing accepted evaluation records remain auditable rather than being silently rewritten after
  the product decision.
