# Phase 5 development batch v1 single-review candidate packet

> Status: Frozen agent-authored candidate packet. Human decision state is recorded only in separate governed artifacts.

## Fixed identities

- Design preregistration: `phase5-development-batch-preregistration-v1`
- Review governance: `phase5-development-single-review-governance-v1`
- Review-governance SHA-256: `a11593ce188abb16c7f3832992cf9c5fe121e6086dacdb5bf1f9009944db1264`
- Governed single reviewer: `sr_001` (decision state external to this packet)
- Governed decision path: `datasets/evaluation/phase5/reviews/development-single-review-v1.decisions.jsonl`
- Validation report path: `reports/evaluation/phase5-development-single-review-v1-validation.json`
- Batch: `pymc-6.1.0-api-phase5-development-batch-v1`
- Candidate SHA-256: `832075827b782c26b4975635f19b836439a2a0d582e36fa59704ee19bbb15abb`
- Corpus hash policy: `canonical-chunk-identity-json-v1`
- Corpus SHA-256: `af0b6d5408b0a9cf22ee56cd536816c9487f04498c874972270c442cf9ecd6b2`
- Candidate count: 24
- Proposed answerable count: 18
- Proposed hard-negative count: 6
- Proposed claim count: 28
- Proposed support-set count: 31
- Referenced chunk count: 10

## Leakage triage boundary

- Normalization policy: `nfkc-casefold-whitespace-v1`
- Exact normalized duplicates are rejected before this packet is rendered.
- Lexical overlap is triage only; it is not retrieval evidence or a leakage decision.
- Every candidate requires human semantic near-duplicate review before entering a reviewed dataset.
- Prior questions: `datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl` (`82c0c625224a23b0f293ac130180a36badb765b39c6dcdea1d797d6b62e64efc`)
- Prior questions: `datasets/evaluation/phase2/pymc_sample_queries.jsonl` (`5df8628e7c22042784cf5361cafbbbc204b8cdc7313f43508dec6e7a8c6eba87`)
- Prior questions: `datasets/evaluation/phase4/pymc_core_queries.jsonl` (`5f5eb1f0e42a77759a5a1b33bae26fa43264002238633ed93a3d0d6695aa454b`)
- Prior questions: `datasets/evaluation/repository-code/pymc_implementation_queries.jsonl` (`3bd9269d140b804594dae5f0c55ac36c8c400150b01ca2120b9c9447b969ce9f`)

## Candidate decisions

For every candidate, the governed workflow requires the single human reviewer to accept, revise, or reject the query, corpus-relative label, claims, and minimal support sets. Human outcomes are not embedded in this packet. This review is not independent adjudication.

### p5dev_v1_query_001

- Slot: `p5dev_v1_slot_001`
- Proposed corpus answerability: `true`
- Query family: `sampling_controls`
- Template family: `direct_function_contract`
- Intent: `api_usage`
- Difficulty: `beginner`
- Expected API symbols: `pymc.sample`
- Hard-negative category: none

#### Proposed query

> If I leave some model variables without an explicit step method, what does `pymc.sample` do for them in PyMC 6.1.0?

#### Proposed claims and support

- `p5dev_v1_query_001_claim_001`: `pymc.sample` automatically assigns step methods to variables that do not have one.
  - Alternative minimal set 1: `chunk_070e4da52bcfccda8d96`

#### Prior-query lexical triage

- Jaccard `0.227273` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_001`: What does pymc.sample do?
- Jaccard `0.227273` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_001`: What does pymc.sample do?
- Jaccard `0.222222` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_007`: Does random_seed accept a legacy RandomState in PyMC 6.1.0?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_002

- Slot: `p5dev_v1_slot_002`
- Proposed corpus answerability: `true`
- Query family: `sampling_controls`
- Template family: `parameter_behavior`
- Intent: `parameter_behavior`
- Difficulty: `beginner`
- Expected API symbols: `pymc.sample`
- Hard-negative category: none

#### Proposed query

> With `blas_cores="auto"`, how does `pymc.sample` choose the total number of active BLAS threads relative to `cores`?

#### Proposed claims and support

- `p5dev_v1_query_002_claim_001`: With `blas_cores="auto"`, `pymc.sample` tries to keep the total number of active BLAS threads equal to `cores`.
  - Alternative minimal set 1: `chunk_070e4da52bcfccda8d96`

#### Prior-query lexical triage

- Jaccard `0.217391` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_003`: What is the default number of draws in pymc.sample?
- Jaccard `0.217391` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_003`: What is the default number of draws in pymc.sample?
- Jaccard `0.192308` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_004`: How does tune affect the number of iterations and are tuning samples discarded?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_003

- Slot: `p5dev_v1_slot_003`
- Proposed corpus answerability: `true`
- Query family: `sampling_controls`
- Template family: `input_constraint`
- Intent: `parameter_behavior`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.sample`
- Hard-negative category: none

#### Proposed query

> When selecting a computational `backend` in `pymc.sample`, what two constraints should I account for regarding installation and `compile_kwargs["mode"]`?

#### Proposed claims and support

- `p5dev_v1_query_003_claim_001`: A selected computational backend may require installing extra dependencies.
  - Alternative minimal set 1: `chunk_070e4da52bcfccda8d96`

- `p5dev_v1_query_003_claim_002`: `compile_kwargs["mode"]` cannot be combined with the `backend` argument.
  - Alternative minimal set 1: `chunk_070e4da52bcfccda8d96`

#### Prior-query lexical triage

- Jaccard `0.200000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_023`: What are dims and coords used for in pymc.Data?
- Jaccard `0.178571` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_018`: Which computational backend values are recommended by pymc.sample in PyMC 6.1.0?
- Jaccard `0.178571` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_018`: Which computational backend values are recommended by pymc.sample in PyMC 6.1.0?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_004

- Slot: `p5dev_v1_slot_004`
- Proposed corpus answerability: `true`
- Query family: `sampling_output_contract`
- Template family: `output_contract`
- Intent: `return_and_storage`
- Difficulty: `beginner`
- Expected API symbols: `pymc.sample`
- Hard-negative category: none

#### Proposed query

> What trace storage does `pymc.sample` use when `trace=None`?

#### Proposed claims and support

- `p5dev_v1_query_004_claim_001`: When `trace=None`, `pymc.sample` uses a `MultiTrace` with underlying `NDArray` trace objects.
  - Alternative minimal set 1: `chunk_070e4da52bcfccda8d96`

#### Prior-query lexical triage

- Jaccard `0.400000` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_001`: What does pymc.sample do?
- Jaccard `0.400000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_001`: What does pymc.sample do?
- Jaccard `0.333333` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_012`: When does pymc.sample return a ZarrTrace?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_005

- Slot: `p5dev_v1_slot_005`
- Proposed corpus answerability: `true`
- Query family: `sampling_output_contract`
- Template family: `input_constraint`
- Intent: `version_sensitive`
- Difficulty: `advanced`
- Expected API symbols: `pymc.sample`
- Hard-negative category: none

#### Proposed query

> In PyMC 6.1.0, what happens if `keep_warning_stat=True`: where are warnings retained, which persistence operations become unavailable, and what default avoids that limitation?

#### Proposed claims and support

- `p5dev_v1_query_005_claim_001`: With `keep_warning_stat=True`, warning objects are retained in the returned `idata.sample_stats` group.
  - Alternative minimal set 1: `chunk_070e4da52bcfccda8d96`

- `p5dev_v1_query_005_claim_002`: Keeping warning objects makes the returned `InferenceData` unable to use `.to_netcdf()` or `.to_zarr()`.
  - Alternative minimal set 1: `chunk_070e4da52bcfccda8d96`

- `p5dev_v1_query_005_claim_003`: The default `keep_warning_stat=False` drops the warning statistic automatically and leaves the `InferenceData` compatible with saving.
  - Alternative minimal set 1: `chunk_070e4da52bcfccda8d96`

#### Prior-query lexical triage

- Jaccard `0.233333` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_018`: Which computational backend values are recommended by pymc.sample in PyMC 6.1.0?
- Jaccard `0.233333` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_018`: Which computational backend values are recommended by pymc.sample in PyMC 6.1.0?
- Jaccard `0.187500` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_022`: Can pymc.Data change value, shape, and dimensionality through pymc.set_data in PyMC 6.1.0?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_006

- Slot: `p5dev_v1_slot_006`
- Proposed corpus answerability: `true`
- Query family: `data_container_contract`
- Template family: `direct_function_contract`
- Intent: `api_usage`
- Difficulty: `beginner`
- Expected API symbols: `pymc.Data`
- Hard-negative category: none

#### Proposed query

> With its default mutability, what type of variable does `pymc.Data` register in the model?

#### Proposed claims and support

- `p5dev_v1_query_006_claim_001`: With the default `mutable=True`, `pymc.Data` registers the variable as a `SharedVariable`.
  - Alternative minimal set 1: `chunk_8087d370d7cb0d682ae2`

#### Prior-query lexical triage

- Jaccard `0.315789` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_003`: What is the default number of draws in pymc.sample?
- Jaccard `0.315789` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_003`: What is the default number of draws in pymc.sample?
- Jaccard `0.277778` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_021`: What does pymc.Data create inside a model?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_007

- Slot: `p5dev_v1_slot_007`
- Proposed corpus answerability: `true`
- Query family: `data_container_contract`
- Template family: `parameter_behavior`
- Intent: `parameter_behavior`
- Difficulty: `beginner`
- Expected API symbols: `pymc.Data`
- Hard-negative category: none

#### Proposed query

> What does `infer_dims_and_coords=True` ask `pymc.Data` to do when the supplied value has an index?

#### Proposed claims and support

- `p5dev_v1_query_007_claim_001`: When enabled and the value has an index, `pymc.Data` tries to infer coordinate values and dimension names from that index.
  - Alternative minimal set 1: `chunk_e254c2d8ed3f2fdf8d8d`

#### Prior-query lexical triage

- Jaccard `0.238095` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_024`: Does pymc.set_data update the shape when data values change?
- Jaccard `0.235294` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_001`: What does pymc.sample do?
- Jaccard `0.235294` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_001`: What does pymc.sample do?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_008

- Slot: `p5dev_v1_slot_008`
- Proposed corpus answerability: `true`
- Query family: `data_container_contract`
- Template family: `procedural_workflow`
- Intent: `api_usage`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.Data`
- Hard-negative category: none

#### Proposed query

> When creating `pymc.Data` from a pandas DataFrame, how can I name dimensions from its columns and request index-based dimension inference?

#### Proposed claims and support

- `p5dev_v1_query_008_claim_001`: For pandas Series or DataFrame values, the `dims` argument names variable dimensions using the Series or DataFrame columns.
  - Alternative minimal set 1: `chunk_e254c2d8ed3f2fdf8d8d`

- `p5dev_v1_query_008_claim_002`: Setting `infer_dims_and_coords=True` asks the container to infer coordinates and dimension names from the value's index.
  - Alternative minimal set 1: `chunk_e254c2d8ed3f2fdf8d8d`

#### Prior-query lexical triage

- Jaccard `0.142857` — `datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl` / `notebook_010`: How do I construct a Gaussian Process covariance function in PyMC?
- Jaccard `0.137931` — `datasets/evaluation/repository-code/pymc_implementation_queries.jsonl` / `code_004`: How does pymc.Data handle a Python list before registering the data container?
- Jaccard `0.129032` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_022`: Can pymc.Data change value, shape, and dimensionality through pymc.set_data in PyMC 6.1.0?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_009

- Slot: `p5dev_v1_slot_009`
- Proposed corpus answerability: `true`
- Query family: `data_update_contract`
- Template family: `direct_function_contract`
- Intent: `api_usage`
- Difficulty: `beginner`
- Expected API symbols: `pymc.model.core.set_data`
- Hard-negative category: none

#### Proposed query

> Can one `pymc.model.core.set_data` call replace more than one registered data-container value?

#### Proposed claims and support

- `p5dev_v1_query_009_claim_001`: `pymc.model.core.set_data` can set the values of one or more data-container variables.
  - Alternative minimal set 1: `chunk_67f1417c989e25a0b269`

#### Prior-query lexical triage

- Jaccard `0.217391` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_022`: Can pymc.Data change value, shape, and dimensionality through pymc.set_data in PyMC 6.1.0?
- Jaccard `0.200000` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_002`: Can pymc.sample use multiple step methods in one call?
- Jaccard `0.200000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_002`: Can pymc.sample use multiple step methods in one call?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_010

- Slot: `p5dev_v1_slot_010`
- Proposed corpus answerability: `true`
- Query family: `data_update_contract`
- Template family: `parameter_behavior`
- Intent: `parameter_behavior`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.model.core.set_data`
- Hard-negative category: none

#### Proposed query

> Is `coords` positional or keyword-only in the PyMC 6.1.0 signature of `pymc.model.core.set_data`?

#### Proposed claims and support

- `p5dev_v1_query_010_claim_001`: The `coords` argument is keyword-only in `pymc.model.core.set_data(new_data, model=None, *, coords=None)`.
  - Alternative minimal set 1: `chunk_0534d7f7dc0ee3d7674b`

#### Prior-query lexical triage

- Jaccard `0.240000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_022`: Can pymc.Data change value, shape, and dimensionality through pymc.set_data in PyMC 6.1.0?
- Jaccard `0.227273` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_003`: What is the default number of draws in pymc.sample?
- Jaccard `0.227273` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_003`: What is the default number of draws in pymc.sample?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_011

- Slot: `p5dev_v1_slot_011`
- Proposed corpus answerability: `true`
- Query family: `data_update_contract`
- Template family: `procedural_workflow`
- Intent: `api_usage`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.model.core.set_data`
- Hard-negative category: none

#### Proposed query

> How does the documented `set_data` example reuse one fitted model on a new observed dataset without recompiling it?

#### Proposed claims and support

- `p5dev_v1_query_011_claim_001`: Inside the existing model context, the example replaces observed `y` through `pm.set_data({"y": new_values})` before sampling again.
  - Alternative minimal set 1: `chunk_f09fd8e15a80db2baf99`

- `p5dev_v1_query_011_claim_002`: Declaring the likelihood with `shape=y.shape` makes its shape track the updated observed data, enabling reuse of the same model without recompilation.
  - Alternative minimal set 1: `chunk_f09fd8e15a80db2baf99`

#### Prior-query lexical triage

- Jaccard `0.166667` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_025`: How does the new_data mapping identify variables in pymc.set_data?
- Jaccard `0.160000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_026`: Can posterior predictive samples use a model different from the fitted model?
- Jaccard `0.153846` — `datasets/evaluation/repository-code/pymc_implementation_queries.jsonl` / `code_004`: How does pymc.Data handle a Python list before registering the data container?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_012

- Slot: `p5dev_v1_slot_012`
- Proposed corpus answerability: `true`
- Query family: `posterior_predictive_controls`
- Template family: `direct_function_contract`
- Intent: `api_usage`
- Difficulty: `beginner`
- Expected API symbols: `pymc.sample_posterior_predictive`
- Hard-negative category: none

#### Proposed query

> What does `pymc.sample_posterior_predictive` condition its forward samples on?

#### Proposed claims and support

- `p5dev_v1_query_012_claim_001`: `pymc.sample_posterior_predictive` generates forward samples conditioned on posterior samples of variables found in the trace.
  - Alternative minimal set 1: `chunk_0f560b5e9847d47c9f2a`

#### Prior-query lexical triage

- Jaccard `0.272727` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_001`: What does pymc.sample do?
- Jaccard `0.272727` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_001`: What does pymc.sample do?
- Jaccard `0.214286` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_021`: What does pymc.Data create inside a model?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_013

- Slot: `p5dev_v1_slot_013`
- Proposed corpus answerability: `true`
- Query family: `posterior_predictive_controls`
- Template family: `parameter_behavior`
- Intent: `parameter_behavior`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.sample_posterior_predictive`
- Hard-negative category: none

#### Proposed query

> Does putting a traced variable only in `var_names` force `pymc.sample_posterior_predictive` to resample it?

#### Proposed claims and support

- `p5dev_v1_query_013_claim_001`: `var_names` controls which variables appear in the output and does not by itself trigger resampling.
  - Alternative minimal set 1: `chunk_4cb92e902495d287e54c`
  - Alternative minimal set 2: `chunk_b533fae009131320ddaa`

#### Prior-query lexical triage

- Jaccard `0.190476` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_007`: Does random_seed accept a legacy RandomState in PyMC 6.1.0?
- Jaccard `0.190476` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_007`: Does random_seed accept a legacy RandomState in PyMC 6.1.0?
- Jaccard `0.166667` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_012`: When does pymc.sample return a ZarrTrace?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_014

- Slot: `p5dev_v1_slot_014`
- Proposed corpus answerability: `true`
- Query family: `posterior_predictive_output_contract`
- Template family: `output_contract`
- Intent: `return_and_storage`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.sample_posterior_predictive`
- Hard-negative category: none

#### Proposed query

> Which output container does `pymc.sample_posterior_predictive` return when `return_inferencedata=False`?

#### Proposed claims and support

- `p5dev_v1_query_014_claim_001`: With `return_inferencedata=False`, `pymc.sample_posterior_predictive` returns a dictionary.
  - Alternative minimal set 1: `chunk_4cb92e902495d287e54c`

#### Prior-query lexical triage

- Jaccard `0.307692` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_012`: When does pymc.sample return a ZarrTrace?
- Jaccard `0.307692` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_012`: When does pymc.sample return a ZarrTrace?
- Jaccard `0.230769` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_010`: What changes when return_inferencedata is false?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_015

- Slot: `p5dev_v1_slot_015`
- Proposed corpus answerability: `true`
- Query family: `posterior_predictive_controls`
- Template family: `output_contract`
- Intent: `return_and_storage`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.sample_posterior_predictive`
- Hard-negative category: none

#### Proposed query

> What happens to the input trace when `extend_inferencedata=True` and the posterior-predictive group already exists?

#### Proposed claims and support

- `p5dev_v1_query_015_claim_001`: With `extend_inferencedata=True`, PyMC uses `DataTree.update()` to add samples to the input trace, modifies it in place, and returns it.
  - Alternative minimal set 1: `chunk_4cb92e902495d287e54c`

- `p5dev_v1_query_015_claim_002`: If the target group already exists, PyMC issues a warning and overwrites that group.
  - Alternative minimal set 1: `chunk_4cb92e902495d287e54c`

#### Prior-query lexical triage

- Jaccard `0.227273` — `datasets/evaluation/repository-code/pymc_implementation_queries.jsonl` / `code_005`: What warning does posterior predictive sampling issue when the model contains Potentials?
- Jaccard `0.130435` — `datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl` / `notebook_001`: What is the difference between support dimensions and batch dimensions in PyMC?
- Jaccard `0.130435` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_026`: Can posterior predictive samples use a model different from the fitted model?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_016

- Slot: `p5dev_v1_slot_016`
- Proposed corpus answerability: `true`
- Query family: `mutable_prediction_workflow`
- Template family: `procedural_workflow`
- Intent: `workflow_composition`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.Data`, `pymc.model.core.set_data`
- Hard-negative category: none

#### Proposed query

> In the `pymc.Data` example that fits one model to several observed datasets, which two operations are repeated for each dataset?

#### Proposed claims and support

- `p5dev_v1_query_016_claim_001`: For each dataset, the example switches the registered `data` value with `model.set_data("data", data_vals)`.
  - Alternative minimal set 1: `chunk_f7d55663f01200eb5f54`

- `p5dev_v1_query_016_claim_002`: After each update, the example calls `pm.sample()` and appends the resulting trace to `idatas`.
  - Alternative minimal set 1: `chunk_f7d55663f01200eb5f54`

#### Prior-query lexical triage

- Jaccard `0.192308` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_023`: What are dims and coords used for in pymc.Data?
- Jaccard `0.185185` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_017`: How are alpha and beta used in the pymc.sample example?
- Jaccard `0.185185` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_017`: How are alpha and beta used in the pymc.sample example?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_017

- Slot: `p5dev_v1_slot_017`
- Proposed corpus answerability: `true`
- Query family: `mutable_prediction_workflow`
- Template family: `input_constraint`
- Intent: `workflow_composition`
- Difficulty: `advanced`
- Expected API symbols: `pymc.Data`, `pymc.model.core.set_data`
- Hard-negative category: none

#### Proposed query

> What model construction lets a likelihood automatically follow the length of a predictor later replaced through `set_data`?

#### Proposed claims and support

- `p5dev_v1_query_017_claim_001`: The example defines predictor `x` with `pm.Data` and declares the likelihood with `shape=x.shape`.
  - Alternative minimal set 1: `chunk_f09fd8e15a80db2baf99`

- `p5dev_v1_query_017_claim_002`: When `pm.set_data` replaces `x`, the data shape changes dynamically and the likelihood shape follows it automatically.
  - Alternative minimal set 1: `chunk_67f1417c989e25a0b269`, `chunk_f09fd8e15a80db2baf99`

#### Prior-query lexical triage

- Jaccard `0.142857` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_021`: What does pymc.Data create inside a model?
- Jaccard `0.130435` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_003`: What is the default number of draws in pymc.sample?
- Jaccard `0.130435` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_003`: What is the default number of draws in pymc.sample?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_018

- Slot: `p5dev_v1_slot_018`
- Proposed corpus answerability: `true`
- Query family: `mutable_prediction_workflow`
- Template family: `procedural_workflow`
- Intent: `workflow_composition`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.model.core.set_data`, `pymc.sample_posterior_predictive`
- Hard-negative category: none

#### Proposed query

> After `pm.set_data` changes a predictor, which downstream quantities are recomputed automatically, which traced random variables remain fixed by default, and how should an `ImplicitFreezeWarning` be handled?

#### Proposed claims and support

- `p5dev_v1_query_018_claim_001`: Deterministics that depend on changed `Data` are recomputed automatically during posterior-predictive generation.
  - Alternative minimal set 1: `chunk_b533fae009131320ddaa`

- `p5dev_v1_query_018_claim_002`: A random variable present in the trace and absent from `sample_vars` keeps its trace value even when an ancestor is volatile.
  - Alternative minimal set 1: `chunk_4cb92e902495d287e54c`
  - Alternative minimal set 2: `chunk_b533fae009131320ddaa`

- `p5dev_v1_query_018_claim_003`: For an `ImplicitFreezeWarning`, the user can opt in to regeneration with `sample_vars` or explicitly retain the trace value with `freeze_vars`.
  - Alternative minimal set 1: `chunk_4cb92e902495d287e54c`
  - Alternative minimal set 2: `chunk_b533fae009131320ddaa`

#### Prior-query lexical triage

- Jaccard `0.125000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_027`: Which dimensions are treated as sample dimensions by default in sample_posterior_predictive?
- Jaccard `0.093750` — `datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl` / `notebook_005`: What variables and operations make up a PyTensor graph?
- Jaccard `0.093750` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_020`: How should I diagnose divergences with ArviZ after sampling?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_019

- Slot: `p5dev_v1_slot_019`
- Proposed corpus answerability: `false`
- Query family: `sampling_controls`
- Template family: `unsupported_guarantee_contrast`
- Intent: `version_sensitive`
- Difficulty: `advanced`
- Expected API symbols: `pymc.sample`
- Hard-negative category: `documented-options-do-not-establish-requested-guarantee`

#### Proposed query

> Does one `random_seed` value guarantee identical posterior draws across the `pymc`, `nutpie`, `blackjax`, and `numpyro` NUTS implementations in PyMC 6.1.0?

#### Proposed claims and support

No claims or support sets are proposed. Review against the complete corpus appendix.

#### Prior-query lexical triage

- Jaccard `0.280000` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_007`: Does random_seed accept a legacy RandomState in PyMC 6.1.0?
- Jaccard `0.280000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_007`: Does random_seed accept a legacy RandomState in PyMC 6.1.0?
- Jaccard `0.250000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_022`: Can pymc.Data change value, shape, and dimensionality through pymc.set_data in PyMC 6.1.0?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_020

- Slot: `p5dev_v1_slot_020`
- Proposed corpus answerability: `false`
- Query family: `sampling_output_contract`
- Template family: `unsupported_operation_contrast`
- Intent: `return_and_storage`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.sample`
- Hard-negative category: `nearby-api-does-not-support-requested-operation`

#### Proposed query

> How can I resume a crashed `pymc.sample` run from a partially written `ZarrTrace` at exactly the next unfinished draw?

#### Proposed claims and support

No claims or support sets are proposed. Review against the complete corpus appendix.

#### Prior-query lexical triage

- Jaccard `0.181818` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_012`: When does pymc.sample return a ZarrTrace?
- Jaccard `0.181818` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_012`: When does pymc.sample return a ZarrTrace?
- Jaccard `0.153846` — `datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl` / `notebook_010`: How do I construct a Gaussian Process covariance function in PyMC?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_021

- Slot: `p5dev_v1_slot_021`
- Proposed corpus answerability: `false`
- Query family: `data_container_contract`
- Template family: `unsupported_guarantee_contrast`
- Intent: `version_sensitive`
- Difficulty: `advanced`
- Expected API symbols: `pymc.Data`
- Hard-negative category: `documented-options-do-not-establish-requested-guarantee`

#### Proposed query

> What documented rule guarantees exactly how every pandas MultiIndex level is converted into coordinates by `pymc.Data(infer_dims_and_coords=True)`?

#### Proposed claims and support

No claims or support sets are proposed. Review against the complete corpus appendix.

#### Prior-query lexical triage

- Jaccard `0.125000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_021`: What does pymc.Data create inside a model?
- Jaccard `0.120000` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_006`: How is cores chosen when cores=None in pymc.sample?
- Jaccard `0.120000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_006`: How is cores chosen when cores=None in pymc.sample?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_022

- Slot: `p5dev_v1_slot_022`
- Proposed corpus answerability: `false`
- Query family: `data_update_contract`
- Template family: `unsupported_operation_contrast`
- Intent: `api_usage`
- Difficulty: `beginner`
- Expected API symbols: `pymc.model.core.set_data`
- Hard-negative category: `nearby-api-does-not-support-requested-operation`

#### Proposed query

> How can I make a multi-variable `pymc.model.core.set_data` update roll back atomically if one replacement fails?

#### Proposed claims and support

No claims or support sets are proposed. Review against the complete corpus appendix.

#### Prior-query lexical triage

- Jaccard `0.153846` — `datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl` / `notebook_006`: Why can a constrained PyMC random variable have a separate transformed value variable?
- Jaccard `0.153846` — `datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl` / `notebook_010`: How do I construct a Gaussian Process covariance function in PyMC?
- Jaccard `0.125000` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_021`: What does pymc.Data create inside a model?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_023

- Slot: `p5dev_v1_slot_023`
- Proposed corpus answerability: `false`
- Query family: `posterior_predictive_controls`
- Template family: `unsupported_guarantee_contrast`
- Intent: `parameter_behavior`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.sample_posterior_predictive`
- Hard-negative category: `documented-options-do-not-establish-requested-guarantee`

#### Proposed query

> Does a fixed `random_seed` guarantee byte-identical posterior-predictive arrays across the `numba`, `c`, and `jax` backends?

#### Proposed claims and support

No claims or support sets are proposed. Review against the complete corpus appendix.

#### Prior-query lexical triage

- Jaccard `0.166667` — `datasets/evaluation/phase4/pymc_core_queries.jsonl` / `q_026`: Can posterior predictive samples use a model different from the fitted model?
- Jaccard `0.160000` — `datasets/evaluation/repository-code/pymc_implementation_queries.jsonl` / `code_005`: What warning does posterior predictive sampling issue when the model contains Potentials?
- Jaccard `0.120000` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_007`: Does random_seed accept a legacy RandomState in PyMC 6.1.0?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

### p5dev_v1_query_024

- Slot: `p5dev_v1_slot_024`
- Proposed corpus answerability: `false`
- Query family: `mutable_prediction_workflow`
- Template family: `unsupported_operation_contrast`
- Intent: `workflow_composition`
- Difficulty: `intermediate`
- Expected API symbols: `pymc.Data`, `pymc.sample_posterior_predictive`
- Hard-negative category: `nearby-api-does-not-support-requested-operation`

#### Proposed query

> How can `pymc.sample_posterior_predictive` derive new out-of-sample coordinate labels automatically from a NumPy predictor update when no `coords` are supplied?

#### Proposed claims and support

No claims or support sets are proposed. Review against the complete corpus appendix.

#### Prior-query lexical triage

- Jaccard `0.178571` — `datasets/evaluation/notebooks/pymc_conceptual_queries.jsonl` / `notebook_009`: Where does sample_posterior_predictive store out-of-sample results when predictions=True?
- Jaccard `0.178571` — `datasets/evaluation/repository-code/pymc_implementation_queries.jsonl` / `code_002`: How does pymc.sample decide whether nutpie can be selected automatically?
- Jaccard `0.160000` — `datasets/evaluation/phase2/pymc_sample_queries.jsonl` / `q_012`: When does pymc.sample return a ZarrTrace?

#### Single-human review checklist

- [ ] Query is realistic, clear, and not a semantic near-duplicate of prior evaluation data.
- [ ] Proposed corpus-relative answerability is correct.
- [ ] Every necessary proposition is an atomic claim, or no claim is valid for this hard negative.
- [ ] Every support set is sufficient and minimal; all valid alternatives are represented.
- [ ] Hard-negative status is confirmed, revised, or marked not applicable.
- [ ] The decision record has a real UTC timestamp and an explicit final status: accepted-as-proposed / accepted-with-revisions / rejected / unresolved.
- [ ] Rejected or unresolved records contain concise review notes and no reviewed dataset content.

## Frozen corpus appendix

The appendix contains all 15 chunks so hard negatives can be reviewed against the complete admitted corpus, not only nearby evidence selected by the agent.

### Evidence `chunk_0534d7f7dc0ee3d7674b`

- Document: `doc_9cabb930971b31b5f763`
- Content SHA-256: `d5c41f29722ded8dadfbb5b2880ee0827c02b620dd0c354f464e70ba614ca64b`
- Source: https://www.pymc.io/projects/docs/en/stable/api/model/generated/pymc.model.core.set_data.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Parameters`
- API symbols: `pymc.model.core.set_data`

    API symbol: pymc.model.core.set_data
    Signature: pymc.model.core.set_data(new_data,model=None,*,coords=None)
    Section: Parameters

    new_data: dict
    New values for the data containers. The keys of the dictionary are the variables’ names in the model and the values are the objects with which to update.

### Evidence `chunk_070e4da52bcfccda8d96`

- Document: `doc_c7542318b80e10fd1370`
- Content SHA-256: `2037c9b679bb478dcfa83e1428940845cf30eaedf2ae45a204fd2048f154965f`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Parameters`
- API symbols: `pymc.sample`

    API symbol: pymc.sample
    Signature: pymc.sample(draws=1000,*,tune=None,chains=None,cores=None,random_seed=None,progressbar=True,progressbar_theme=None,quiet=False,step=None,var_names=None,nuts_sampler=None,initvals=None,init='auto',jitter_max_retries=10,n_init=200000,trace=None,discard_tuned_samples=True,compute_convergence_checks=True,keep_warning_stat=False,return_inferencedata=True,idata_kwargs=None,nuts_sampler_kwargs=None,callback=None,mp_ctx=None,blas_cores='auto',model=None,backend=None,compile_kwargs=None,**kwargs)
    Section: Parameters

    draws `int`
    The number of samples to draw. Defaults to 1000. The number of tuned samples are discarded by default. See `discard_tuned_samples` .

    tune `int`
    Number of iterations to tune, defaults to 1000. Samplers adjust the step sizes, scalings or similar during tuning. Tuning samples will be drawn in addition to the number specified in the `draws` argument, and will be discarded unless `discard_tuned_samples` is set to False.

    chains `int`
    The number of chains to sample. Running independent chains is important for some convergence statistics and can also reveal multiple modes in the posterior. If `None` , then set to either `cores` or 2, whichever is larger.

    cores `int`
    The number of chains to run in parallel. If `None` , set to the number of CPUs in the system, but at most 4.

    random_seed `int` , array_like of `int` , or `Generator` , optional
    Random seed(s) used by the sampling steps. Each step will create its own `Generator` object to make its random draws in a way that is indepedent from all other steppers and all other chains. A `TypeError` will be raised if a legacy `RandomState` object is passed. We no longer support `RandomState` objects because their seeding mechanism does not allow easy spawning of new independent random streams that are needed by the step methods.

    progressbar: bool or ProgressType, optional
    How and whether to display the progress bar. If False, no progress bar is displayed. Otherwise, you can ask for one of the following: - “combined”: A single progress bar that displays the total progress across all chains. Only timing

    information is shown.

    - “split”: A separate progress bar for each chain. Only timing information is shown.
    - “combined+stats” or “stats+combined”: A single progress bar displaying the total progress across all
    chains. Aggregate sample statistics are also displayed.
    - “split+stats” or “stats+split”: A separate progress bar for each chain. Sample statistics for each chain
    are also displayed.

    If True, the default is “split+stats” is used.

    quiet bool , default `False`
    If True, suppress all logging output and progress bars during sampling. This is useful when sampling in loops or when no output is desired. When True, this overrides `progressbar=True` .

    step `function` or iterable of `functions`
    A step function or collection of functions. If there are variables without step methods, step methods for those variables will be assigned automatically. By default the NUTS step method will be used, if appropriate to the model.

    var_names `list` of `str` , optional
    Names of variables to be stored in the trace. Defaults to all free variables and deterministics.

    nuts_sampler `str` , optional
    Which NUTS implementation to run. One of [“pymc”, “nutpie”, “blackjax”, “numpyro”]. This requires the chosen sampler to be installed. All samplers, except “pymc”, require the full model to be continuous. If `None` (default), “nutpie” is used if installed and can be compiled to the desired backend.

    blas_cores: int or “auto” or None, default = “auto”
    The total number of threads blas and openmp functions should use during sampling. Setting it to “auto” will ensure that the total number of active blas threads is the same as the cores argument. If set to an integer, the sampler will try to use that total number of blas threads. If blas_cores is not divisible by cores , it might get rounded down. If set to None, this will keep the default behavior of whatever blas implementation is used at runtime. Note that this argument is ignored when using fork multiprocessing start method.

    initvals optional, `dict` , `array` of `dict`
    Dict or list of dicts with initial value strategies to use instead of the defaults from Model.initial_values . The keys should be names of transformed random variables. Initialization methods for NUTS (see `init` keyword) can overwrite the default.

    init `str`
    Initialization method to use for auto-assigned NUTS samplers. See pm.init_nuts for a list of all options. This argument is ignored when manually passing the NUTS step method. Only applicable to the pymc nuts sampler.

    jitter_max_retries `int`
    Maximum number of repeated attempts (per chain) at creating an initial matrix with uniform jitter that yields a finite probability. This applies to `jitter+adapt_diag` and `jitter+adapt_full` init methods.

    n_init `int`
    Number of iterations of initializer. Only works for ‘ADVI’ init methods.

    trace `backend` , optional
    A backend instance or None. If `None` , a `MultiTrace` object with underlying `NDArray` trace objects is used. If `trace` is a `ZarrTrace` instance, the drawn samples will be written onto the desired storage while sampling is on-going. This means sampling runs that, for whatever reason, die in the middle of their execution will write the partial results onto the storage. If the storage persist on disk, these results should be available even after a server crash. See `ZarrTrace` for more information.

    discard_tuned_samples bool
    Whether to discard posterior samples of the tune interval.

    compute_convergence_checks bool , default=True
    Whether to compute sampler statistics like Gelman-Rubin and `effective_n` .

    keep_warning_stat bool
    If `True` the “warning” stat emitted by, for example, HMC samplers will be kept in the returned `idata.sample_stats` group. This leads to the `idata` not supporting `.to_netcdf()` or `.to_zarr()` and should only be set to `True` if you intend to use the “warning” objects right away. Defaults to `False` such that the `"warning"` stat is dropped automatically, making the `InferenceData` compatible with saving.

    return_inferencedata bool
    Whether to return the trace as an `arviz:arviz.InferenceData` (True) object or a MultiTrace (False). Defaults to True .

    idata_kwargs `dict` , optional
    Keyword arguments for `pymc.to_inference_data()`

    nuts_sampler_kwargs `dict` , optional
    Deprecated. Pass NUTS keyword arguments via `nuts={...}` instead (e.g. `pm.sample(...,nuts={"target_accept":0.9})` ).

    callback `function` , default=None
    A function which gets called for every sample from the trace of a chain. The function is called with the trace and the current draw and will contain all samples for a single trace. the `draw.chain` argument can be used to determine which of the active chains the sample is drawn from. Sampling can be interrupted by throwing a `KeyboardInterrupt` in the callback.

    mp_ctx `multiprocessing.context.BaseContent`
    A multiprocessing context for parallel sampling. See multiprocessing documentation for details.

    model `Model` (optional `if` `in` `with` `context` )
    Model to sample from. The model needs to have free random variables.

    backend: str, optional.
    Which computational backend to use. Recommended to be one of “numba”, “c”, and “jax”. May require installing extra dependencies.

    compile_kwargs: dict, optional
    Dictionary with keyword argument to pass to the functions compiled by the step methods. `compile_kwargs["mode"]` cannot be combined with `backend` .

### Evidence `chunk_0f560b5e9847d47c9f2a`

- Document: `doc_9411eb3cb4de154ce8e3`
- Content SHA-256: `0c9e40fb9c8bc188707074d70075602acf5ba3e183e70b488477a5142163da2d`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample_posterior_predictive.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Overview`
- API symbols: `pymc.sample_posterior_predictive`

    API symbol: pymc.sample_posterior_predictive
    Signature: pymc.sample_posterior_predictive(trace,model=None,*,var_names=None,sample_vars=None,freeze_vars=None,sample_dims=None,random_seed=None,progressbar=True,progressbar_theme=<rich.theme.Themeobject>,return_inferencedata=True,extend_inferencedata=False,predictions=False,idata_kwargs=None,backend=None,compile_kwargs=None)
    Section: Overview

    Generate forward samples for var_names , conditioned on the posterior samples of variables found in the trace .

    This method can be used to perform different kinds of model predictions, including posterior predictive checks.

    The matching of unobserved model variables, and posterior samples in the trace is made based on the variable names. Therefore, a different model than the one used for posterior sampling may be used for posterior predictive sampling, as long as the variables whose posterior we want to condition on have the same name, and compatible shape and coordinates.

### Evidence `chunk_19342001ac28c7109268`

- Document: `doc_c7542318b80e10fd1370`
- Content SHA-256: `0f42abf6a4f6474c81f5742e5106252d8833d8985e0d4a96498f228d1e4a1785`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Returns`
- API symbols: `pymc.sample`

    API symbol: pymc.sample
    Signature: pymc.sample(draws=1000,*,tune=None,chains=None,cores=None,random_seed=None,progressbar=True,progressbar_theme=None,quiet=False,step=None,var_names=None,nuts_sampler=None,initvals=None,init='auto',jitter_max_retries=10,n_init=200000,trace=None,discard_tuned_samples=True,compute_convergence_checks=True,keep_warning_stat=False,return_inferencedata=True,idata_kwargs=None,nuts_sampler_kwargs=None,callback=None,mp_ctx=None,blas_cores='auto',model=None,backend=None,compile_kwargs=None,**kwargs)
    Section: Returns

    trace `pymc.backends.base.MultiTrace` | `pymc.backends.zarr.ZarrTrace` | `arviz.InferenceData`
    A `MultiTrace` , `InferenceData` or `ZarrTrace` object that contains the samples. A `ZarrTrace` is only returned if the supplied `trace` argument is a `ZarrTrace` instance. Refer to `ZarrTrace` for the benefits this backend provides.

### Evidence `chunk_3b18e70cd47d4b07c688`

- Document: `doc_9411eb3cb4de154ce8e3`
- Content SHA-256: `e45f83468fe765100e9fb3d02b690ebf1a58b93fe4cd38ff4b595933ddb4d7d0`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample_posterior_predictive.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Returns`
- API symbols: `pymc.sample_posterior_predictive`

    API symbol: pymc.sample_posterior_predictive
    Signature: pymc.sample_posterior_predictive(trace,model=None,*,var_names=None,sample_vars=None,freeze_vars=None,sample_dims=None,random_seed=None,progressbar=True,progressbar_theme=<rich.theme.Themeobject>,return_inferencedata=True,extend_inferencedata=False,predictions=False,idata_kwargs=None,backend=None,compile_kwargs=None)
    Section: Returns

    `DataTree` or `Dict`
    A `DataTree` object containing the posterior predictive samples (default), or a dictionary with variable names as keys, and samples as numpy arrays.

### Evidence `chunk_4cb92e902495d287e54c`

- Document: `doc_9411eb3cb4de154ce8e3`
- Content SHA-256: `0b7f6ed42d29338dfa9f9a1cedb38dd6dcaa3629fda2fec0afe97914419b4980`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample_posterior_predictive.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Parameters`
- API symbols: `pymc.sample_posterior_predictive`

    API symbol: pymc.sample_posterior_predictive
    Signature: pymc.sample_posterior_predictive(trace,model=None,*,var_names=None,sample_vars=None,freeze_vars=None,sample_dims=None,random_seed=None,progressbar=True,progressbar_theme=<rich.theme.Themeobject>,return_inferencedata=True,extend_inferencedata=False,predictions=False,idata_kwargs=None,backend=None,compile_kwargs=None)
    Section: Parameters

    trace `backend` , `list` , `Dataset` , `DataTree` , or `MultiTrace`
    Trace generated from MCMC sampling, or a list of dicts (eg. points or from `find_MAP()` ), or `xarray.Dataset` (eg. DataTree.posterior or DataTree.prior)

    model `Model` (optional `if` `in` `with` `context` )
    Model to be used to generate the posterior predictive samples. It will generally be the model used to generate the trace , but it doesn’t need to be.

    sample_vars `str` or `list` of `str` , optional
    Random variables or deterministics to regenerate on each draw rather than copy from the trace. Regeneration propagates volatility downstream: an RV that is in the trace and not listed here keeps its trace value, but if one of its ancestors is volatile (listed here, or a changed Data/coord) an `ImplicitFreezeWarning` flags it so the user can opt in by adding it here, or silence the warning via `freeze_vars` . Empty by default — RVs missing from the trace (including observed RVs) are always regenerated automatically. Cannot overlap with `freeze_vars` .

    freeze_vars `str` or `list` of `str` , optional
    Trace variables (RVs or deterministics) to reuse from the trace. Cannot overlap with `sample_vars` . Trace RVs not in `sample_vars` are already implicitly frozen, so the practical effect of listing an RV here is to silence its `ImplicitFreezeWarning` . Deterministics don’t trigger that warning at all — a volatile deterministic just recomputes with the current upstream values — so listing one only matters when you want to keep the trace value instead (see example below).

    var_names `str` or `list` of `str` , optional
    Controls only which variables appear in the output; does not trigger resampling. Each listed name is either computed fresh or copied from the input trace, depending on whether it or any of its upstream is volatile (see the behavior section below). Defaults to `sample_vars` when that is specified; otherwise (the classic posterior-predictive default) to the observed variables plus any deterministic that depends on these.

    sample_dims `list` of `str` , optional
    Dimensions over which to loop and generate posterior predictive samples. When `sample_dims` is `None` (default) both “chain” and “draw” are considered sample dimensions. Only taken into account when trace is DataTree or Dataset.

    random_seed `int` , `RandomState` or `Generator` , optional
    Seed for the random number generator.

    progressbar bool
    Whether to display a progress bar in the command line. The bar shows the percentage of completion, the sampling speed in samples per second (SPS), and the estimated remaining time until completion (“expected time of arrival”; ETA).

    return_inferencedata bool , default `True`
    Whether to return an `xarray.DataTree` (True) object or a dictionary (False).

    extend_inferencedata bool , default `False`
    Whether to automatically use `xarray.DataTree.update()` to add the posterior predictive samples to trace or not. If True, trace is modified inplace but still returned. If the DataTree already contains a group that would be added (e.g. `posterior_predictive` ), a warning is issued and the existing group is overwritten.

    predictions bool , default `False`
    Flag used to set the location of posterior predictive samples within the returned `DataTree` object. If False, assumes samples are generated based on the fitting data to be used for posterior predictive checks, and samples are stored in the `posterior_predictive` . If True, assumes samples are generated based on out-of-sample data as predictions, and samples are stored in the `predictions` group.

    idata_kwargs `dict` , optional
    Keyword arguments for `pymc.to_inference_data()` if `predictions=False` or to `pymc.predictions_to_inference_data()` otherwise.

    backend: str, optional
    Which computational backend to use. Recommended to be one of “numba”, “c”, and “jax”.

    compile_kwargs: dict, optional
    Keyword arguments for `pymc.pytensorf.compile()` . `compile_kwargs["mode"]` cannot be combined with `backend` .

### Evidence `chunk_67f1417c989e25a0b269`

- Document: `doc_9cabb930971b31b5f763`
- Content SHA-256: `7cb333f8bcef0279053b99d508b63ad9d14ffc812f67dd534338a88f1fbc18c1`
- Source: https://www.pymc.io/projects/docs/en/stable/api/model/generated/pymc.model.core.set_data.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Overview`
- API symbols: `pymc.model.core.set_data`

    API symbol: pymc.model.core.set_data
    Signature: pymc.model.core.set_data(new_data,model=None,*,coords=None)
    Section: Overview

    Set the value of one or more data container variables.

    Note that the shape is also dynamic, it is updated when the value is changed. See the examples below for two common use-cases that take advantage of this behavior.

### Evidence `chunk_8087d370d7cb0d682ae2`

- Document: `doc_16037e242e11d70fa4d5`
- Content SHA-256: `5c21c0706e6365349d6e2a884e96bfde13975b4b7b8e034f49d536d6e7ff2fac`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.Data.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Overview`
- API symbols: `pymc.Data`

    API symbol: pymc.Data
    Signature: pymc.Data(name,value,*,dims=None,coords=None,infer_dims_and_coords=False,model=None,**kwargs)
    Section: Overview

    Create a data container that registers a data variable with the model.

    Depending on the `mutable` setting (default: True), the variable is registered as a `SharedVariable` , enabling it to be altered in value and shape, but NOT in dimensionality using `pymc.set_data()` .

    To set the value of the data container variable, check out `pymc.Model.set_data()` .

    When making predictions or doing posterior predictive sampling, the shape of the registered data variable will most likely need to be changed. If you encounter an PyTensor shape mismatch error, refer to the documentation for `pymc.model.set_data()` .

    For more information, read the notebook Using Data Containers .

### Evidence `chunk_b533fae009131320ddaa`

- Document: `doc_9411eb3cb4de154ce8e3`
- Content SHA-256: `92a21afdebc039140471df2270da5bcac6dd09726f566f1901c1716b180fe58a`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample_posterior_predictive.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Examples`
- API symbols: `pymc.sample_posterior_predictive`

    API symbol: pymc.sample_posterior_predictive
    Signature: pymc.sample_posterior_predictive(trace,model=None,*,var_names=None,sample_vars=None,freeze_vars=None,sample_dims=None,random_seed=None,progressbar=True,progressbar_theme=<rich.theme.Themeobject>,return_inferencedata=True,extend_inferencedata=False,predictions=False,idata_kwargs=None,backend=None,compile_kwargs=None)
    Section: Examples

    Posterior predictive checks and predictions

    #

    The most common use of sample_posterior_predictive is to perform posterior predictive checks (in-sample predictions) and new model predictions (out-of-sample predictions). Deterministics that depend on `Data` are recomputed automatically when the data changes — no extra work needed:

    ```python
    import pymc as pm

    with pm.Model(coords={"trial": [0, 1, 2]}) as model:
        x = pm.Data("x", [-1, 0, 1], dims=["trial"])
        beta = pm.Normal("beta")
        noise = pm.HalfNormal("noise")
        linpred = pm.Deterministic("linpred", x * beta, dims=["trial"])
        y = pm.Normal("y", mu=linpred, sigma=noise, observed=[-2, 0, 3], dims=["trial"])

        idata = pm.sample()

        # in-sample posterior predictive
        posterior_predictive = pm.sample_posterior_predictive(idata).posterior_predictive

    with model:
        pm.set_data({"x": [-2, 2]}, coords={"trial": [3, 4]})
        # out-of-sample predictions. `linpred` is recomputed with the new `x`
        # (and the trace's `beta`); `y` is resampled from the new `linpred`.
        pm.sample_posterior_predictive(idata, predictions=True, extend_inferencedata=True)
    ```

    Freezing deterministics

    #

    A deterministic is normally recomputed whenever its inputs change. Occasionally, though, a deterministic captures something that should stay anchored to the training data — e.g. an HSGP standardization computed from `pm.Data` that must not be rederived from the prediction data. Pass the deterministic in `freeze_vars` to keep its trace value:

    ```python
    import pymc as pm

    with pm.Model() as model:
        x = pm.Data("x", [1.0, 2.0, 3.0])
        x_mean = pm.Deterministic("x_mean", x.mean())
        centered = pm.Deterministic("centered", x - x_mean)
        mu = pm.Normal("mu")
        obs = pm.Normal("obs", mu + centered, 1, observed=[0, 0, 0])

        idata = pm.sample()

    # New x values. Without freezing, `x_mean` would be recomputed as the new mean.
    with model:
        pm.set_data({"x": [100.0, 200.0, 300.0]})
        pm.sample_posterior_predictive(idata, freeze_vars=["x_mean"])
    ```

    Forcing a deterministic to recompute

    #

    If `do()` swaps a new expression into a deterministic while every RV and Data value stays unchanged, `sample_posterior_predictive` sees nothing volatile and reuses the deterministic from the trace. List it in `sample_vars` to force recomputation from the current graph:

    ```python
    with pm.Model() as model:
        x = pm.Normal("x")
        pm.Deterministic("det", x**2)
        pm.Normal("obs", model["det"], 1, observed=[0.0])
        idata = pm.sample()

    with pm.do(model, {model["det"]: model["x"] ** 3}) as intervened_model:
        # Force recomputation using the new `x**3` graph.
        pm.sample_posterior_predictive(idata, sample_vars=["det", "obs"])
    ```

    Using different models

    #

    It’s common to use the same model for posterior and posterior predictive sampling, but this is not required. The matching between unobserved model variables and posterior samples is based on the name alone.

    For the last example we could have created a new predictions model. Since the new `y` has no observations, we request it via `sample_vars` argument.

    ```python
    import pymc as pm

    with pm.Model(coords={"trial": [0, 1, 2]}) as train_model:
        x = pm.Data("x", [-1, 0, 1], dims=["trial"])
        beta = pm.Normal("beta")
        noise = pm.HalfNormal("noise")
        y = pm.Normal("y", mu=x * beta, sigma=noise, observed=[-2, 0, 3], dims=["trial"])

        idata = pm.sample()

    with pm.Model(coords={"trial": [3, 4]}) as prediction_model:
        x = pm.Data("x", [-2, 2], dims=["trial"])
        beta = pm.Normal("beta")
        noise = pm.HalfNormal("noise")
        y = pm.Normal("y", mu=x * beta, sigma=noise, dims=["trial"])

        predictions = pm.sample_posterior_predictive(
            idata,
            sample_vars=["y"],
            predictions=True,
        )
    ```

    The new model may even have a different structure and unobserved variables that don’t exist in the trace. These variables will be sampled automatically because they have no trace values to fall back on. In the following example we added a new `extra_noise` variable between the inferred posterior `noise` and the new StudentT observational distribution `y` :

    ```python
    with pm.Model(coords={"trial": [3, 4]}) as distinct_predictions_model:
        x = pm.Data("x", [-2, 2], dims=["trial"])
        beta = pm.Normal("beta")
        noise = pm.HalfNormal("noise")
        extra_noise = pm.HalfNormal("extra_noise", sigma=noise)
        y = pm.StudentT("y", nu=4, mu=x * beta, sigma=extra_noise, dims=["trial"])

        predictions = pm.sample_posterior_predictive(idata, var_names=["y"], predictions=True)
    ```

    For more about out-of-model predictions, see this blog post .

    The behavior of

    sample_vars

    ,

    freeze_vars

    , and

    var_names

    #

    Each of these three arguments controls one aspect of the operation:

    - `sample_vars` — trace variables to treat as volatile: regenerate them (from their distribution or expression) instead of copying from the trace. Empty by default.
    - `freeze_vars` — which trace variables to reuse explicitly (silences the implicit-freeze warning below).
    - `var_names` — which variables appear in the output. Does not trigger resampling of variables in the trace. Defaults to `sample_vars` .

    Volatility. Volatility originates from three sources — variables listed in `sample_vars` , changed Data/coords, and RVs missing from the trace (including observed RVs, which are always regenerated since they have no trace value to reuse). It then propagates downstream through deterministics and other RVs. An RV that is in the trace and not listed in `sample_vars` keeps its trace value — even when one of its ancestors is being resampled. This prevents a single `sample_vars=["x"]` call, or a `set_data` call, from silently invalidating the posterior values for every downstream variable. When an auto-frozen trace variable has a volatile ancestor, an `ImplicitFreezeWarning` flags it so the user can opt in by adding it to `sample_vars` (to resample) or opt out by adding it to `freeze_vars` (to silence the warning while keeping the trace value). The log lists all the RVs being resampled in any given call.

    The following examples use this model:

    ```python
    from logging import getLogger
    import pymc as pm

    # Some environments like google colab suppress
    # the default logging output of PyMC
    getLogger("pymc").setLevel("INFO")

    kwargs = {"progressbar": False, "random_seed": 0}

    with pm.Model() as model:
        x = pm.Normal("x")
        y = pm.Normal("y")
        z = pm.Normal("z", x + y**2)
        det = pm.Deterministic("det", pm.math.exp(z))
        obs = pm.Normal("obs", det, 1, observed=[20])

        idata = pm.sample(tune=10, draws=10, chains=2, **kwargs)
    ```

    Default behavior: Generate samples of `obs` conditioned on the posterior samples of `z` found in the trace. These are often referred to as posterior predictive samples in the literature:

    ```python
    with model:
        pm.sample_posterior_predictive(idata, **kwargs)
        # Sampling: [obs]
    ```

    Copy the trace values for `z` and `det` . Nothing is resampled without explicit sample_vars :

    ```python
    with model:
        pm.sample_posterior_predictive(idata, var_names=["z", "det"], **kwargs)
        # Sampling: []
    ```

    Generate new samples of z and det, conditioned on the posterior samples of x and y found in the trace.

    ```python
    with model:
        pm.sample_posterior_predictive(idata, var_names=["z", "det"], sample_vars=["z"], **kwargs)
        # Sampling: [z]
    ```

    Generate samples of y, z and det, conditioned on the posterior samples of x found in the trace.

    Warning

    The samples of `y` are equivalent to its prior, since it does not depend on any other variables.

    In contrast, the samples of `z` and `det` depend on the new samples of `y` and the posterior samples of `x` found in the trace.

    ```python
    with model:
        pm.sample_posterior_predictive(idata, var_names=["y", "z", "det"], sample_vars=["y", "z"], **kwargs)
        # Sampling: [y, z]
    ```

    Note that if `z` is not placed in sample_vars it won’t be resampled even though it depends on the freshly drawn `y` — cascade stops at RVs that are in the trace. A warning flags this behavior for `z` :

    ```python
    with model:
        pm.sample_posterior_predictive(idata, var_names=["y", "z", "det"], sample_vars=["y"], **kwargs)
        # ImplicitFreezeWarning: 'z' (ancestor is resampled (y))
        # Sampling: [y]
    ```

    If this is the intended behavior z can be added to freeze_vars explicitly, and the warning is avoided.

    ```python
    with model:
        pm.sample_posterior_predictive(idata, var_names=["y", "z", "det"], sample_vars=["y"], freeze_vars=["z"], **kwargs)
        # Sampling: [y]
    ```

    Passing every RV to `sample_vars` makes this equivalent to `sample_prior_predictive()` . Including `obs` in `sample_vars` is redundant — it isn’t in the trace so it is always regenerated:

    ```python
    with model:
        pm.sample_posterior_predictive(
            idata,
            var_names=["x", "y", "z", "det", "obs"],
            sample_vars=["x", "y", "z", "obs"],
            **kwargs,
        )
        # Sampling: [obs, x, y, z]
    ```

    Controlling the number of samples

    #

    You can manipulate the DataTree to control the number of samples

    ```python
    import pymc as pm

    with pm.Model() as model:
        ...
        idata = pm.sample()
    ```

    Generate 1 posterior predictive sample for every 5 posterior samples.

    ```python
    thinned_idata = idata.sel(draw=slice(None, None, 5))
    with model:
        idata.update(pm.sample_posterior_predictive(thinned_idata))
    ```

    Generate 5 posterior predictive samples for every posterior sample.

    ```python
    expanded_idata = idata.copy()
    expanded_idata.posterior = idata.posterior.expand_dims(pred_id=5)
    with model:
        pm.sample_posterior_predictive(
            expanded_idata,
            sample_dims=["chain", "draw", "pred_id"],
            extend_inferencedata=True,
        )
    ```

### Evidence `chunk_b65fd20e8dd52ffab212`

- Document: `doc_c7542318b80e10fd1370`
- Content SHA-256: `b915073a18f89f2fe3ef4e73b5121861629076586e6301e5054818fa728187b0`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Examples`
- API symbols: `pymc.sample`

    API symbol: pymc.sample
    Signature: pymc.sample(draws=1000,*,tune=None,chains=None,cores=None,random_seed=None,progressbar=True,progressbar_theme=None,quiet=False,step=None,var_names=None,nuts_sampler=None,initvals=None,init='auto',jitter_max_retries=10,n_init=200000,trace=None,discard_tuned_samples=True,compute_convergence_checks=True,keep_warning_stat=False,return_inferencedata=True,idata_kwargs=None,nuts_sampler_kwargs=None,callback=None,mp_ctx=None,blas_cores='auto',model=None,backend=None,compile_kwargs=None,**kwargs)
    Section: Examples

    ```python
    In [1]: import pymc as pm
       ...: n = 100
       ...: h = 61
       ...: alpha = 2
       ...: beta = 2

    In [2]: with pm.Model() as model: # context management
       ...:     p = pm.Beta("p", alpha=alpha, beta=beta)
       ...:     y = pm.Binomial("y", n=n, p=p, observed=h)
       ...:     idata = pm.sample()

    In [3]: az.summary(idata, kind="stats")

    Out[3]:
        mean     sd  hdi_3%  hdi_97%
    p  0.609  0.047   0.528    0.699
    ```

### Evidence `chunk_bdbac941d4ebd7c396ed`

- Document: `doc_c7542318b80e10fd1370`
- Content SHA-256: `bf317aa8978a92105ff80dfaa37015d752eebc08f2826f75ba57732b876ccad7`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Overview`
- API symbols: `pymc.sample`

    API symbol: pymc.sample
    Signature: pymc.sample(draws=1000,*,tune=None,chains=None,cores=None,random_seed=None,progressbar=True,progressbar_theme=None,quiet=False,step=None,var_names=None,nuts_sampler=None,initvals=None,init='auto',jitter_max_retries=10,n_init=200000,trace=None,discard_tuned_samples=True,compute_convergence_checks=True,keep_warning_stat=False,return_inferencedata=True,idata_kwargs=None,nuts_sampler_kwargs=None,callback=None,mp_ctx=None,blas_cores='auto',model=None,backend=None,compile_kwargs=None,**kwargs)
    Section: Overview

    Draw samples from the posterior using the given step methods.

    Multiple step methods are supported via compound step methods.

### Evidence `chunk_d63299c2a9cfdb46bd8f`

- Document: `doc_c7542318b80e10fd1370`
- Content SHA-256: `4fa22051cf34f1ebc3aa28f30dc19cff579ba6983861a07e764c913dddf30f6e`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Notes`
- API symbols: `pymc.sample`

    API symbol: pymc.sample
    Signature: pymc.sample(draws=1000,*,tune=None,chains=None,cores=None,random_seed=None,progressbar=True,progressbar_theme=None,quiet=False,step=None,var_names=None,nuts_sampler=None,initvals=None,init='auto',jitter_max_retries=10,n_init=200000,trace=None,discard_tuned_samples=True,compute_convergence_checks=True,keep_warning_stat=False,return_inferencedata=True,idata_kwargs=None,nuts_sampler_kwargs=None,callback=None,mp_ctx=None,blas_cores='auto',model=None,backend=None,compile_kwargs=None,**kwargs)
    Section: Notes

    Optional keyword arguments can be passed to `sample` to be delivered to the `step_method` s used during sampling.

    For example:

    - `target_accept` to NUTS: nuts={‘target_accept’:0.9}
    - `transit_p` to BinaryGibbsMetropolis: binary_gibbs_metropolis={‘transit_p’:.7}

    Note that available step names are:

    `nuts` , `hmc` , `metropolis` , `binary_metropolis` , `binary_gibbs_metropolis` , `categorical_gibbs_metropolis` , `DEMetropolis` , `DEMetropolisZ` , `slice`

    The NUTS step method has several options including:

    - target_accept : float in [0, 1]. The step size is tuned such that we approximate this acceptance rate. Higher values like 0.9 or 0.95 often work better for problematic posteriors. This argument can be passed directly to sample.
    - max_treedepth : The maximum depth of the trajectory tree
    - step_scale : float, default 0.25 The initial guess for the step size scaled down by \(1/n**(1/4)\) , where n is the dimensionality of the parameter space

    Alternatively, if you manually declare the `step_method` s, within the `step`
    kwarg, then you can address the `step_method` kwargs directly. e.g. for a CompoundStep comprising NUTS and BinaryGibbsMetropolis, you could send

    ```python
    step = [
        pm.NUTS([freeRV1, freeRV2], target_accept=0.9),
        pm.BinaryGibbsMetropolis([freeRV3], transit_p=0.7),
    ]
    ```

    You can find a full list of arguments in the docstring of the step methods.

### Evidence `chunk_e254c2d8ed3f2fdf8d8d`

- Document: `doc_16037e242e11d70fa4d5`
- Content SHA-256: `2a6407028f016ce7c4d117f013994494ec1d215cb6ed132873686fb1b9d4308b`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.Data.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Parameters`
- API symbols: `pymc.Data`

    API symbol: pymc.Data
    Signature: pymc.Data(name,value,*,dims=None,coords=None,infer_dims_and_coords=False,model=None,**kwargs)
    Section: Parameters

    name `str`
    The name for this variable.

    value array_like or `pandas.Series` , `pandas.Dataframe`
    A value to associate with this variable.

    dims `str` , `tuple` of `str` or `tuple` of `None` , optional
    Dimension names of the random variables (as opposed to the shapes of these random variables). Use this when `value` is a pandas Series or DataFrame. The `dims` will then be the name of the Series / DataFrame’s columns. See ArviZ documentation for more information about dimensions and coordinates: arviz:quickstart . If this parameter is not specified, the random variables will not have dimension names.

    coords `dict` , optional
    Coordinate values to set for new dimensions introduced by this `Data` variable.

    export_index_as_coords bool
    Deprecated, previous version of “infer_dims_and_coords”

    infer_dims_and_coords bool , default=False
    If True, the `Data` container will try to infer what the coordinates and dimension names should be if there is an index in `value` .

    **kwargs `dict` , optional
    Extra arguments passed to `pytensor.shared()` .

### Evidence `chunk_f09fd8e15a80db2baf99`

- Document: `doc_9cabb930971b31b5f763`
- Content SHA-256: `dbfb0f7afb2638773f2ed0ee4ea4be3eacf5e96041abf005c6fffc64351ee5e0`
- Source: https://www.pymc.io/projects/docs/en/stable/api/model/generated/pymc.model.core.set_data.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Examples`
- API symbols: `pymc.model.core.set_data`

    API symbol: pymc.model.core.set_data
    Signature: pymc.model.core.set_data(new_data,model=None,*,coords=None)
    Section: Examples

    This example shows how to change the shape of the likelihood to correspond automatically with x , the predictor in a regression model.

    ```python
    import pymc as pm

    with pm.Model() as model:
        x = pm.Data("x", [1.0, 2.0, 3.0])
        y = pm.Data("y", [1.0, 2.0, 3.0])
        beta = pm.Normal("beta", 0, 1)
        obs = pm.Normal("obs", x * beta, 1, observed=y, shape=x.shape)
        idata = pm.sample()
    ```

    Then change the value of x to predict on new data.

    ```python
    with model:
        pm.set_data({'x': [5., 6., 9., 12., 15.]})
        y_test = pm.sample_posterior_predictive(idata)

    print(y_test.posterior_predictive['obs'].mean(('chain', 'draw')))

    >>> array([4.6088569 , 5.54128318, 8.32953844, 11.14044852, 13.94178173])
    ```

    This example shows how to reuse the same model without recompiling on a new data set. The shape of the likelihood, obs , automatically tracks the shape of the observed data, y .

    ```python
    import numpy as np
    import pymc as pm

    rng = np.random.default_rng()
    data = rng.normal(loc=1.0, scale=2.0, size=100)

    with pm.Model() as model:
        y = pm.Data("y", data)
        theta = pm.Normal("theta", mu=0.0, sigma=10.0)
        obs = pm.Normal("obs", theta, 2.0, observed=y, shape=y.shape)
        idata = pm.sample()
    ```

    Now update the model with a new data set.

    ```python
    with model:
        pm.set_data({"y": rng.normal(loc=1.0, scale=2.0, size=200)})
        idata = pm.sample()
    ```

### Evidence `chunk_f7d55663f01200eb5f54`

- Document: `doc_16037e242e11d70fa4d5`
- Content SHA-256: `0ccda38a377fb74b71ab1cb11d3a28521487bd4b8ae038a33c543e695486b38f`
- Source: https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.Data.html
- Library: `pymc` `6.1.0`
- Source type: `api_reference`
- Section: `Examples`
- API symbols: `pymc.Data`

    API symbol: pymc.Data
    Signature: pymc.Data(name,value,*,dims=None,coords=None,infer_dims_and_coords=False,model=None,**kwargs)
    Section: Examples

    ```python
    >>> import pymc as pm
    >>> import numpy as np
    >>> # We generate 10 datasets
    >>> true_mu = [np.random.randn() for _ in range(10)]
    >>> observed_data = [mu + np.random.randn(20) for mu in true_mu]
    ```

    ```python
    >>> with pm.Model() as model:
    ...     data = pm.Data("data", observed_data[0])
    ...     mu = pm.Normal("mu", 0, 10)
    ...     pm.Normal("y", mu=mu, sigma=1, observed=data)
    ```

    ```python
    >>> # Generate one trace for each dataset
    >>> idatas = []
    >>> for data_vals in observed_data:
    ...     with model:
    ...         # Switch out the observed dataset
    ...         model.set_data("data", data_vals)
    ...         idatas.append(pm.sample())
    ```
