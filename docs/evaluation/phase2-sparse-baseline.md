# Phase 2 sparse retrieval baseline

## Scope

This experiment validates the complete local path from a controlled PyMC source to ranked
chunks and a stored evaluation report. It does not estimate retrieval quality for the wider
PyMC, ArviZ, or PyTensor documentation.

The corpus contains one official PyMC 6.1.0 `pymc.sample` API page split into five semantic
chunks: Overview, Parameters, Returns, Notes, and Examples. The dataset contains 20 manually
curated English questions: 18 answerable questions with binary qrels and two questions whose
answers are absent from the corpus.

## Reproduce

```bash
uv run rag-pymc ingest \
  --manifest datasets/raw/manifests/pymc/6.1.0/pymc.sample.json \
  --source datasets/fixtures/pymc/6.1.0/pymc.sample.html \
  --output-dir datasets/processed/local

uv run rag-pymc evaluate \
  --dataset datasets/evaluation/phase2/pymc_sample_queries.jsonl \
  --corpus-dir datasets/processed/local \
  --output reports/evaluation/phase2-bm25-baseline.json \
  --top-k 3 \
  --seed 20260719 \
  --k1 1.5 \
  --b 0.75
```

## Configuration

- Retriever: `bm25-v1`
- Tokenizer: `technical-v1`
- BM25: `k1=1.5`, `b=0.75`
- Rank cutoff: `k=3`
- Corpus chunks: 5
- Dataset SHA-256: `5df8628e7c22042784cf5361cafbbbc204b8cdc7313f43508dec6e7a8c6eba87`
- Corpus SHA-256: `8f1329ac43e8b4c93667c96f87094ac114be87a6b99f99b489cab32b017bf21e`

## Results

| Metric | Result |
| --- | ---: |
| Recall@3 | 1.000000 |
| Precision@3 | 0.351852 |
| Hit Rate@3 | 1.000000 |
| MRR | 0.842593 |
| nDCG@3 | 0.882933 |
| Version correctness | 1.000000 |
| Correct abstention | 0.000000 |
| Mean retrieved tokens | 1460.3 |
| Mean latency | 0.037982 ms |
| p50 latency | 0.037469 ms |
| p95 latency | 0.046981 ms |

Latency is an in-process measurement over five chunks on one local run. It is recorded for
provenance and is not a representative production benchmark.

## Interpretation

Every answerable query retrieved all judged chunks within the first three positions, but the
MRR and nDCG results show that the relevant chunk was not consistently ranked first. The low
Precision@3 partly reflects the small number of relevant chunks per query and its fixed
three-result denominator.

Both unanswerable questions returned three chunks. This is expected from the baseline policy:
any positive lexical overlap is returned, and no score threshold or abstention classifier is
implemented. The result establishes a concrete failure rather than supporting an abstention
claim.

The mean retrieved-token count is high relative to a five-chunk corpus because the Parameters
section is one large retrieval unit. Splitting API parameters into child chunks is now a
testable hypothesis for a structure-aware chunking experiment.

## Limitations

- The answerable qrels target the same single page used to design the dataset.
- The dataset does not yet cover cross-document ambiguity, synonymous terminology, or hard
  negatives from other APIs.
- Binary qrels do not distinguish highly relevant from partially relevant chunks.
- The current token count is a retrieval-token estimate, not a generator context-window count.
- No parameter or threshold was tuned after observing these results.

## Next experiment

Phase 3 should add a dense retriever behind the existing `Retriever` contract and compare
sparse and dense rankings on an expanded official-source corpus. Before drawing comparative
conclusions, add hard negatives and more API symbols; preserve this BM25 configuration as the
unchanged reference baseline.
