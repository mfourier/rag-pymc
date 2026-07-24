# Probabilistic Modeling Workflow

Use this workflow for a new model or a material change to an existing one. Each stage answers a different question; do not collapse computational success, statistical calibration, and scientific usefulness into one claim.

## 1. Specify the data-generating process

Write down:

- the observational unit and sampling mechanism;
- the outcome support and measurement process;
- predictors, offsets, censoring, truncation, exposure, or missingness;
- latent structure, grouping, time dependence, or spatial dependence;
- the estimand and the prediction target;
- conditional independence assumptions;
- which mechanisms are outside scope.

Identify whether the likelihood represents the actual observation process. A convenient distribution with the right mean is not sufficient when dispersion, zero inflation, censoring, selection, or dependence are consequential.

## 2. Choose a parameterization and priors

Map parameters to valid support. Use transformed scales when they make constraints and geometry clearer: log scales for positive magnitudes, logits for probabilities, and Cholesky factors for covariance structures.

Express prior implications in domain units. Mark each prior as one of:

- domain-informed;
- regularizing but weakly informative;
- sensitivity alternative;
- temporary assumption due to insufficient information.

For hierarchical location-scale models, consider centered and non-centered parameterizations as competing computational representations. Do not declare either universally superior; performance depends on group information, scale, and posterior geometry.

## 3. Encode dimensions explicitly

Define stable coordinates on the model when arrays represent named entities. Attach `dims` to data, latent variables, and likelihoods. Verify the relationship among:

- support dimensions belonging to one draw from a distribution;
- batch dimensions representing independent or broadcasted draws;
- sample dimensions such as `chain` and `draw` in posterior containers.

Read `pytensor-and-dimensions.md` before implementing multivariate, hierarchical, mixture, or custom distributions.

## 4. Check the prior predictive distribution

Use `pm.sample_prior_predictive` before fitting. Examine observables and derived quantities in their natural units. Ask whether simulated data include impossible, physically implausible, or decision-irrelevant regimes.

A plausible marginal range is not enough. Check dependence, group heterogeneity, temporal patterns, category probabilities, and extremes when the model encodes them. Revise priors or structure based on explicit domain constraints, not on the desire to reproduce the observed data before fitting.

## 5. Inspect the graph and log probability

Before expensive sampling:

- inspect model variables, coordinates, and shapes;
- evaluate or draw deterministic components on small fixtures;
- compile the model log probability when useful;
- verify finite initial log probability;
- check that indexing and broadcasting represent the intended generative process.

Use symbolic expressions inside the model. A value available through `.eval()` is only a debugging realization, not a replacement for a symbolic dependency.

## 6. Sample the posterior

Use multiple independent chains and explicit seeds. Choose draws based on the precision required for posterior functionals, not a universal count. Preserve tuning separately from retained draws.

Prefer the default PyMC sampler unless the model or deployment constraints justify another compatible backend. Verify optional sampler packages before selecting them. Record sampler, backend, seed, chains, tuning, retained draws, and relevant configuration.

## 7. Diagnose computation

Use `diagnostics-and-criticism.md`. At minimum, inspect:

- rank-normalized split R-hat;
- bulk and tail ESS;
- MCSE for reported quantities;
- divergences and their parameter locations;
- trace or rank plots;
- tree-depth and energy behavior when relevant.

Resolve material pathologies before interpreting posterior summaries. More draws reduce Monte Carlo error only when the chain is sampling the intended stationary distribution adequately.

## 8. Criticize the fitted model

Generate posterior predictive replications and compare discrepancies tied to the scientific question. Examine both central behavior and consequential tails or subgroup patterns.

Posterior predictive agreement does not prove that latent parameters are identified or causally interpretable. Report what aspect of the observable distribution was checked and what remains unchecked.

Run sensitivity analysis when conclusions may depend on priors, likelihood family, parameterization, missing-data assumptions, or influential observations.

## 9. Predict or compare

For out-of-sample prediction, register predictors with `pm.Data`, update them with `pm.set_data`, update coordinates when length changes, and request `predictions=True` from `pm.sample_posterior_predictive`.

For model comparison, ensure models target the same observed units and comparable predictive task. Compute pointwise log likelihood, inspect Pareto diagnostics for LOO, and interpret ELPD differences with their uncertainty. Do not choose a model from a scalar ranking alone; predictive adequacy and scientific assumptions still matter.

## 10. Calibrate when required

Sampling diagnostics operate on fitted chains; they do not by themselves test whether an inference procedure is calibrated across repeated simulated datasets. For algorithm or implementation validation with simulation-based calibration, invoke `$simulation-based-calibration` and preserve its assumptions, rank/PIT handling, and limitations.

## 11. Report limitations

Summarize:

- the generative assumptions and inferential target;
- the evidence supporting priors and likelihood;
- computational diagnostics and thresholds actually inspected;
- predictive checks and their discrepancy measures;
- sensitivity results;
- version and seed information;
- unresolved scientific, identification, approximation, or computational limitations.
