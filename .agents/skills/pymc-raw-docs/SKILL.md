---
name: pymc-raw-docs
description: Search, inspect, summarize, and assess the local upstream PyMC documentation sources under datasets/raw/source. Use when Codex needs to locate PyMC concepts or symbols in raw Markdown, reStructuredText, or notebooks; answer with file-level evidence; investigate documentation structure; select or chunk sources for the rag-pymc corpus; or identify version and provenance limitations before relying on these files.
---

# PyMC Raw Documentation

Use the upstream documentation tree as local discovery and contextual evidence while preserving its uncertain version boundary. Do not treat it as the controlled PyMC 6.1.0 corpus.

## Establish the source boundary

1. Work from the `rag-pymc` repository root and confirm that `datasets/raw/source` exists.
2. Read `references/source-map.md` before selecting sources. Re-read it when the tree changes materially.
3. Inspect `datasets/raw/manifests/pymc/6.1.0` when the question requires controlled PyMC 6.1.0 evidence.
4. Confirm executable behavior against `pyproject.toml`, `uv.lock`, and the pinned environment when an answer will influence repository code.

The raw tree has no adjacent acquisition manifest proving a release tag, commit, or complete-tree hash. Notebook outputs expose several historical or development PyMC versions, but none versions the entire tree. Never describe this directory as PyMC 6.1.0 or as an immutable release snapshot without new provenance evidence.

## Locate evidence

Classify the request and search the smallest relevant scope:

- Consult `learn/`, `guides/`, and `glossary.md` for conceptual explanations and worked examples.
- Consult `api/` for module organization and autosummary symbol discovery. Most RST API files list symbols but do not contain the generated signatures or docstrings.
- Consult `contributing/` only for PyMC development, documentation, release, or contribution workflows.
- Consult notebook source cells for executable narratives. Ignore stored outputs unless the request explicitly concerns recorded output or environment metadata.

Search plain-text sources and notebook inputs with:

```bash
python .agents/skills/pymc-raw-docs/scripts/search_docs.py \
  "posterior predictive" --scope learn
```

Use a regular expression for symbol variants or related phrases:

```bash
python .agents/skills/pymc-raw-docs/scripts/search_docs.py \
  'sample_posterior_predictive|predictions=True' --regex
```

If an exact phrase has no result, retry with two to five discriminative terms rather than scanning every large notebook. Use `rg -n` for targeted Markdown/RST follow-up and inspect the surrounding section with `sed`. For notebooks, prefer the search script because it excludes generated outputs.

## Interpret evidence

1. Read the complete relevant section, including nearby warnings and code blocks. Do not answer from an isolated match.
2. Follow MyST and Sphinx references only as far as needed. Recognize `autosummary` entries as symbol inventory, not generated API documentation.
3. Compare duplicate or overlapping pages before relying on one copy. Record the chosen relative source path.
4. Separate:
   - **Raw-source statement**: directly supported by a named file or notebook cell.
   - **Pinned-runtime behavior**: verified in the repository environment.
   - **Inference**: derived from the source rather than explicitly documented.
   - **Recommendation**: a project or modeling choice requiring judgment.
5. Report conflicts between raw source, controlled snapshots, and the pinned runtime. Follow controlled snapshots or runtime evidence for version-sensitive implementation.

## Use the tree for corpus work

When selecting or preparing ingestion sources:

1. Exclude navigation-only, error, promotional, and contributor pages unless they serve the target query distribution.
2. Extract notebook Markdown and code inputs without stored outputs, execution renderings, or binary images.
3. Preserve heading hierarchy, code blocks, MyST/RST directives that affect meaning, and the relative source path.
4. Deduplicate overlapping guides by normalized content rather than filename alone.
5. Assign distinct source types for conceptual guides, notebooks, API indexes, and contributor documentation.
6. Create acquisition metadata with upstream URL, release/tag or commit, license, per-file hashes, acquisition time, parser version, and chunker version before calling the result reproducible.
7. Evaluate the expanded corpus separately; do not compare retrieval metrics across changed corpora as though only the retriever changed.

## Deliver the result

Cite exact repository-relative paths and notebook cell numbers when applicable. State the source boundary once when version-sensitive claims are present. Keep excerpts short, preserve code exactly when it matters, and say explicitly when the raw tree does not contain enough evidence.
