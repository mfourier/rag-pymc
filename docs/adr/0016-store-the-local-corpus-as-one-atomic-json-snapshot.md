# ADR-0016: Store the local corpus as one atomic JSON snapshot

- Status: Accepted
- Date: 2026-07-28
- Supersedes: ADR-0003

## Context

ADR-0003 selected two deterministic JSON Lines files for documents and chunks. Each file was
replaced atomically, but an interruption between replacements could expose a new document set with
stale chunks, or the reverse. The MVP has one local writer, four documents, and 15 chunks, so
streaming two files has no measured benefit.

## Decision

Store the complete active corpus in one versioned `corpus.json` object containing sorted document
and chunk arrays. Validate uniqueness, ordering, and every chunk-to-document reference whenever the
snapshot is read. Upserts write a temporary file and atomically replace the one visible snapshot.

Keep the project-owned repository interface. A database is still unwarranted for the current local,
single-writer workload.

## Consequences

- Readers observe documents and chunks from the same committed snapshot.
- The format remains deterministic, inspectable, offline, and content-addressed at the record level.
- Corruption and incomplete parent references fail closed when loading.
- The entire small corpus is rewritten for an upsert; this is acceptable for the MVP and must be
  revisited if corpus size or write concurrency becomes material.
- Historical JSONL evaluation datasets are unaffected; this decision applies only to processed
  corpus persistence.
