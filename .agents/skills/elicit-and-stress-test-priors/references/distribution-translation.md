# Translating Prior Knowledge into Distributions

## Start with Support and Units

Match the distribution to the quantity:

- real-valued location: Normal or Student-t when symmetry is defensible;
- positive scale: half-Normal, half-Student-t, lognormal, or Gamma depending on tail and near-zero beliefs;
- probability: Beta, logistic-Normal, or a structured hierarchical prior;
- rate: Gamma or lognormal, often through a log link;
- correlation matrix: a valid joint correlation prior rather than independent pairwise correlations;
- simplex: Dirichlet or logistic-Normal depending on desired dependence;
- ordered values: an ordered transformation with a prior on gaps or unconstrained increments.

Support compatibility is necessary but not sufficient. Inspect density near boundaries, tail behavior, and induced observable behavior.

## Quantile Matching

For a Normal prior with median or mean `m` and central probability `p` inside `[L, U]`, symmetry implies:

```text
mu = (L + U) / 2
sigma = (U - L) / (2 * z)
```

where `z` is the standard-Normal quantile at `(1 + p) / 2`. If the elicited interval is asymmetric, use two or more quantiles and solve numerically or choose an asymmetric family.

For a lognormal prior, elicit quantiles on the natural positive scale and solve on the log scale:

```text
log(q_p) = mu_log + sigma_log * z_p
```

This often makes multiplicative judgments easier to express.

For a Beta prior, two quantiles generally require numerical solution. Mean `m` and concentration `kappa` give:

```text
alpha = m * kappa
beta = (1 - m) * kappa
```

Treat “effective prior sample size” interpretations cautiously when the likelihood is not binomial or the prior was not constructed from exchangeable trials.

## Translate Link-Scale Coefficients

### Logistic regression

A coefficient `beta` changes odds by `exp(beta)` per one-unit predictor increase. Elicit plausible odds ratios only after defining the predictor scale. Standardization changes the meaning of one unit and must be documented.

Check probabilities across realistic covariate combinations. Independent broad priors on an intercept and slopes can imply near-deterministic probabilities over much of the design matrix.

### Log-link models

`exp(beta)` is a multiplicative change in the conditional mean or rate. Check induced counts or event rates, exposure ranges, and tail behavior.

### Identity-link models

Coefficient units follow the outcome per predictor unit. Check that generated means and outcomes remain plausible across the covariate domain.

## Scale Priors in Hierarchical Models

The prior on a group-level standard deviation determines pooling and the prevalence of extreme groups. Validate it by simulating:

- between-group differences;
- the maximum and minimum group effects for the actual number of groups;
- shrinkage under realistic group sample sizes;
- induced outcomes for both typical and extreme groups.

A half-distribution with a large scale can place substantial mass on implausibly heterogeneous populations. A prior with density near zero can still permit meaningful variation.

## Correlations and Joint Structure

Do not assign independent priors to correlations that must form a positive-definite matrix. Choose a joint construction and inspect:

- marginal correlations;
- partial correlations;
- eigenvalues and condition numbers;
- implied covariance at plausible marginal scales;
- effects on observable group trajectories.

If only certain correlation patterns are scientifically plausible, encode and test that structure rather than relying on a generic matrix prior.

## Heavy Tails and Mixtures

Heavy-tailed priors can protect against over-shrinkage but may generate extreme predictions and difficult posterior geometry. Mixture or spike-and-slab priors introduce label, multimodality, and computational considerations. Use them only when the scientific meaning of components or sparsity is explicit.

Robustness is not created merely by selecting a Student-t family. Inspect how tail mass propagates through nonlinear links and interactions.

## Truncation and Hard Constraints

Use hard bounds for physical or logical impossibility, not convenience. When a boundary is plausible, examine posterior mass near it and sampler geometry. A soft prior that makes implausible values rare may express uncertainty better than truncation.

Ordering, monotonicity, and conservation constraints can create strong joint information. Report them as prior assumptions.

## Prior Predictive Translation

For every proposed joint prior:

1. draw parameter values;
2. compute latent means and decision-relevant quantities;
3. draw observations from the likelihood;
4. summarize familiar rates, maxima, zero counts, group differences, slopes, and extremes;
5. compare with physical, historical, or expert constraints;
6. revise with a documented reason.

Parameter-space plausibility does not guarantee observable-space plausibility.
