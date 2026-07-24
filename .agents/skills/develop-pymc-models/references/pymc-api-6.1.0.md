# PyMC 6.1.0 API Notes

These notes target the repository's pinned runtime. Verify exact signatures with `inspect.signature` before using uncommon arguments. The controlled sources are the matching HTML snapshots and JSON manifests in `datasets/fixtures/pymc/6.1.0/` and `datasets/raw/manifests/pymc/6.1.0/`.

## Compatibility guard

The installed PyMC 6.1.0 runtime does not expose `pm.dims`. Do not copy examples using the experimental `pymc.dims` module from newer online documentation. In this project, use model `coords`, distribution `dims`, and explicit `shape` only where necessary.

Mutable `stable` pages can display a release newer than the pinned environment. Treat such pages as conceptual context, not proof that code runs here.

## `pm.sample`

`pm.sample` draws posterior samples using assigned step methods. In PyMC 6.1.0:

- `draws` defaults to 1,000 retained samples per chain.
- `tune` defaults to 1,000 additional tuning iterations; tuning samples are discarded by default.
- independent chains support between-chain diagnostics and can expose separate modes.
- `cores=None` uses the detected CPU count capped at four.
- integer seeds, integer sequences, and NumPy `Generator` values are supported; legacy `RandomState` is rejected.
- documented `nuts_sampler` choices include `pymc`, `nutpie`, `blackjax`, and `numpyro`, but optional packages must be installed separately.
- pass PyMC NUTS settings through `nuts={"target_accept": 0.9}` rather than relying on a signature from another release.
- the default structured return is a DataTree in the pinned runtime; `return_inferencedata=False` requests a `MultiTrace`. A supplied `ZarrTrace` produces that backend type.

Use explicit seeds and preserve multiple chains. Avoid suppressing convergence checks in production. A minimal smoke run may disable them only when the test explicitly does not make inferential claims.

## `pm.Data`

`pm.Data` creates and registers a model data variable. Use it when values must be replaced without rebuilding the graph.

- `dims` names its dimensions.
- `coords` supplies coordinate values for dimensions introduced by that variable.
- `pm.set_data` can change a registered value and its shape.
- `pm.set_data` cannot change the variable's number of dimensions.

Use fixed data only when replacement is not part of fitting, prediction, or testing. Do not assume mutable data will correct incompatible broadcasting elsewhere in the graph.

## `pm.set_data`

Call `pm.set_data({"predictor_name": new_values}, coords={...})` inside the model context or pass the model explicitly. Mapping keys identify registered data variables by name. When the number of observations changes, update the corresponding coordinates as well as the data.

Keep feature axes, category encodings, and number of dimensions compatible with the fitted graph. Validate unseen categorical levels explicitly rather than letting integer indexing fail deep in compilation.

## `pm.sample_prior_predictive`

Use prior predictive samples to inspect the consequences of priors and the generative graph before conditioning on observations. The pinned signature defaults to 500 draws. Pass an explicit seed. Validate the names and dimensions of returned groups instead of depending on an unstated container layout.

## `pm.sample_posterior_predictive`

Posterior variables are matched to model variables by name, with compatible shapes and coordinates required. Consequently, posterior predictive sampling may use a structurally compatible model different from the fitted model, but name coincidence alone is insufficient evidence of compatibility.

- sample dimensions default to `chain` and `draw` when `sample_dims=None`.
- in-sample replications use the `posterior_predictive` group by default.
- out-of-sample results use the `predictions` group when `predictions=True`.
- data-dependent deterministics are recomputed after registered data change.
- use `extend_inferencedata=True` only when mutating the supplied posterior container is intentional.
- reason carefully about `var_names`, `sample_vars`, and `freeze_vars`; requesting a downstream variable can require resampling its ancestors.

For prediction, use the sequence:

```python
with model:
    pm.set_data(
        {"x": x_new},
        coords={"observation": np.arange(x_new.shape[0])},
    )
    predictions = pm.sample_posterior_predictive(
        idata,
        var_names=["y"],
        predictions=True,
        random_seed=seed,
    )
```

Use English names and import NumPy as `np` in the surrounding module.

## Pointwise log likelihood

PyMC 6.1.0 exposes `pm.compute_log_likelihood`. Use it when the posterior container lacks a `log_likelihood` group required for predictive comparison. Alternatively, request log likelihood through sampling configuration when the pinned signature supports it. Verify the returned group and observation dimensions before passing it to ArviZ.

## Local source map

Use these files for exact project evidence:

- `datasets/raw/manifests/pymc/6.1.0/pymc.sample.json`
- `datasets/fixtures/pymc/6.1.0/pymc.sample.html`
- `datasets/raw/manifests/pymc/6.1.0/pymc.Data.json`
- `datasets/fixtures/pymc/6.1.0/pymc.Data.html`
- `datasets/raw/manifests/pymc/6.1.0/pymc.model.core.set_data.json`
- `datasets/fixtures/pymc/6.1.0/pymc.model.core.set_data.html`
- `datasets/raw/manifests/pymc/6.1.0/pymc.sample_posterior_predictive.json`
- `datasets/fixtures/pymc/6.1.0/pymc.sample_posterior_predictive.html`

The Phase 4 evaluation set in `datasets/evaluation/phase4/pymc_core_queries.jsonl` provides executable routing cases for these APIs. It is an evaluation artifact, not an additional authority beyond the controlled source pages.
