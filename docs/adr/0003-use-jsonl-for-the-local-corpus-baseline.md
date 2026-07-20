# ADR-0003: Use JSONL for the local corpus baseline

- Status: Accepted
- Date: 2026-07-19

## Context

Phase 1 needs persistent documents and chunks, but it has one source, no concurrent writers,
and no measured query workload. Introducing PostgreSQL or a vector database now would add
migrations and operational state before their requirements are known.

The persisted format must remain inspectable, deterministic, testable without services, and
replaceable through a project-owned repository interface.

## Decision

Use two JSON Lines files for the local baseline:

- `documents.jsonl` contains validated `Document` records;
- `chunks.jsonl` contains validated `Chunk` records.

The repository upserts by deterministic ID, replaces chunks belonging to a re-ingested
document, sorts records by ID, and writes each file through a temporary file followed by an
atomic replace.

Processed local output is ignored by Git. Controlled raw fixtures, source manifests, and
evaluation datasets remain versioned.

## Alternatives considered

### PostgreSQL from the first ingestion slice

It offers transactions and indexed filtering but adds a service, migrations, and CI setup
without a current workload. It was deferred.

### SQLite

It would provide transactions with low operational cost, but JSONL is easier to inspect and
sufficient for the current single-writer corpus.

### Deterministic JSONL behind a repository interface

This minimizes infrastructure while preserving a migration boundary. This alternative was
selected.

## Consequences

- Tests and experiments can build a corpus without external services.
- Repeated ingestion is idempotent for identical artifacts.
- Atomic replacement protects each file individually, but the pair is not a transactional
  database snapshot.
- Concurrent writers are unsupported.
- The decision must be revisited when corpus size, concurrent updates, metadata filtering, or
  operational APIs justify a database.
