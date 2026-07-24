# PyTensor Graphs and Dimensions

Use this reference for custom expressions, shape problems, multivariate distributions, hierarchical indexing, and reusable data containers.

## Think symbolically

PyMC constructs a PyTensor graph. Creating a symbolic expression records operations; it does not immediately compute an array. Compilation turns the graph into an executable function and may optimize it.

Inside a model:

- use PyMC distributions to create random variables;
- use `pm.math` or `pytensor.tensor` for transformations;
- keep dependencies symbolic until sampling or explicit compilation;
- use `.eval()` only for local debugging with concrete graph inputs;
- use `model.compile_logp()` or other model compilation helpers to inspect executable model functions.

Do not use a NumPy operation merely because it accepts an object at model-construction time. Confirm that it preserves the symbolic graph and gradients. Avoid Python branching on symbolic values; express branch logic with symbolic operations.

## Separate dimension types

Distinguish:

- **Support dimensions**: the dimensions of one draw from a distribution. A multivariate normal vector has one support dimension; a matrix-valued distribution may have two.
- **Batch dimensions**: repeated or broadcasted draws outside the support. PyMC and PyTensor conventionally place batch dimensions to the left of support dimensions.
- **Sample dimensions**: dimensions introduced by inference, normally `chain` and `draw`.

Named `dims` describe batch or modeled axes in the output; they do not change the intrinsic support of a distribution. Check each distribution's parameter shape requirements rather than expecting a name to repair incompatible tensors.

## Prefer coordinates and named dimensions

For a hierarchical model, establish coordinates such as:

```python
coords = {
    "group": group_labels,
    "observation": np.arange(y.shape[0]),
}
```

Then attach dimensions consistently:

```python
with pm.Model(coords=coords) as model:
    group_index = pm.Data("group_index", group_codes, dims="observation")
    group_offset = pm.Normal("group_offset", 0.0, 1.0, dims="group")
    mu = pm.Deterministic(
        "mu",
        intercept + group_scale * group_offset[group_index],
        dims="observation",
    )
    pm.Normal("y", mu=mu, sigma=sigma, observed=y, dims="observation")
```

Use this as a structural pattern, not a substantive prior recommendation. The likelihood and prior scales require domain justification.

## Diagnose shapes systematically

When a shape error occurs:

1. Write the expected support, batch, and sample dimensions for every affected variable.
2. Inspect concrete input shapes and coordinate lengths.
3. Inspect distribution parameter shapes before random-variable output shapes.
4. Reduce to a tiny synthetic fixture that preserves the axes.
5. Draw from the prior or evaluate an intermediate symbolic expression.
6. Add an explicit assertion or test once the intended contract is known.

Do not solve shape errors by repeatedly inserting singleton axes without explaining which axis they represent. Do not rely on implicit broadcasting across semantically different dimensions.

## Mutable data constraints

`pm.Data` can change values and axis lengths through `pm.set_data`, but the number of dimensions remains fixed. When an observation axis changes length:

- update every registered array using that axis;
- update the coordinate values;
- preserve feature and support axes expected by parameter tensors;
- validate category codes against fitted category coordinates.

Keep immutable training metadata outside the mutable graph when it should not change during prediction.

## Custom likelihoods and operations

Prefer a built-in PyMC distribution when it represents the observation process. For a custom log probability:

- specify support and parameter constraints explicitly;
- return elementwise or reduced log probability with the intended observation axes;
- preserve differentiability when using gradient-based samplers;
- provide a random sampler if prior or posterior predictive simulation depends on it;
- test normalization or known special cases where feasible;
- compare gradients or log probability against an independent implementation on small inputs.

If an operation breaks gradients, do not assume NUTS remains valid. Either provide a differentiable PyTensor operation with a correct gradient or select and justify a compatible inference method.

## Version boundary

The live PyMC documentation can contain the experimental `pymc.dims` API, but PyMC 6.1.0 in this project has no `pm.dims` attribute. Use conventional `coords` and `dims` syntax until the project deliberately upgrades and tests that module.
