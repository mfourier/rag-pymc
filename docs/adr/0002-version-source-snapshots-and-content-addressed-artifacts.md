# ADR-0002: Version source snapshots and content-addressed artifacts

- Status: Accepted
- Date: 2026-07-19

## Context

Retrieval answers must cite the exact library version used during ingestion. Documentation
aliases such as `stable` are mutable, and the PyMC custom Read the Docs domain did not expose
a working immutable `v6.1.0` page during acquisition. A URL alone is therefore insufficient
to reproduce a corpus.

Cloning or forking the complete PyMC repository would preserve source history, but the first
slice only needs one generated API page. It would also leave the generated HTML build and its
dependencies unspecified.

## Decision

Each acquired source artifact has a versioned manifest containing:

- manifest schema version;
- library and library version;
- published URL, release tag, release URL, and source commit when available;
- server last-modified time and local acquisition time;
- media type and expected API symbol;
- license name and URL;
- SHA-256 of the exact acquired bytes.

Controlled fixtures are checked into `datasets/fixtures`; manifests are checked into
`datasets/raw/manifests`. The fetch boundary verifies the raw hash before parsing.

Normalized document IDs are derived from the normalized document content hash. Chunk IDs are
derived from document ID, semantic section name, and chunk content hash. Re-ingesting identical
inputs with the same transformations therefore produces identical IDs.

Parser and chunker versions are stored on processed artifacts so transformation behavior can
be included in future corpus-build provenance.

## Alternatives considered

### Reference mutable documentation URLs only

This is small but cannot detect content drift and was rejected.

### Clone or fork the entire upstream repository

This preserves Git history but does not identify a generated documentation build and is
unnecessarily broad for the first ingestion slice.

### Store exact snapshots with manifests and hashes

This gives byte-level verification while allowing acquisition to grow one controlled source at
a time. This alternative was selected.

## Consequences

- A mutable published URL is acceptable only when paired with exact release metadata and a raw
  content hash.
- Fixture updates require an intentional manifest and test update.
- Changed normalized content produces new document and chunk IDs.
- Hash identity detects change but does not explain it; future corpus builds must also record
  configuration and code version.
- Large future source sets should move to an artifact store without changing the manifest
  contract.
