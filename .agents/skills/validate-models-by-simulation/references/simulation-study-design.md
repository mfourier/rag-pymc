# Designing a Bayesian Validation Study by Simulation

## 1. Define the Validation Claim

Write one falsifiable statement, such as:

- the posterior median estimates a treatment contrast with acceptable bias across the prespecified regime;
- a 90% credible interval has close to 90% repeated-simulation coverage under the generator;
- the design separates within-group noise from between-group variation;
- predictions remain calibrated under a stated measurement-error process;
- the selected action has acceptable expected regret.

Name the estimand, data-generating regime, procedure, tolerance, and intended use. Avoid “the model works.”

## 2. Separate Experimental Components

Version independently:

- scenario specification;
- parameter or latent-state generator;
- observation generator;
- missingness or measurement process;
- fitted model;
- inference configuration;
- post-processing and target calculation;
- metric summarizer.

When generator and fitter share helper code, a common implementation bug can create false reassurance. Add unit tests against analytic cases or independent calculations where feasible.

## 3. Build a Scenario Grid

Include scenarios along dimensions that can change inferential behavior:

- small, moderate, and intended sample sizes;
- weak and strong signal;
- low and high noise;
- few and many groups;
- balanced and imbalanced groups;
- parameters near boundaries or rare-event rates;
- low and high predictor correlation;
- varying missingness, censoring, or measurement error;
- short and long time series or spatial ranges;
- typical and extreme covariate distributions.

Use a factorial grid when interactions matter, or a space-filling design when the parameter region is large. Weight scenarios only when a target operating distribution is defensible; retain unweighted stress scenarios separately.

## 4. Add Misspecification Deliberately

Generate from plausible alternatives not present in the fitter:

- heavier or lighter tails;
- nonlinear effects fit as linear;
- omitted interactions or latent subgroups;
- overdispersion or zero generation;
- nonexchangeable groups;
- time drift or dependence;
- differential measurement error;
- informative missingness or selection;
- incorrect link or variance function.

Each mismatch should correspond to a real concern. Record whether the goal is robustness, detection through checks, or graceful degradation.

## 5. Define Quantities Before Simulation

Include:

- primary estimands;
- predictive targets at representative and extreme covariates;
- interval endpoints or exceedance probabilities;
- decisions and utilities;
- nuisance quantities linked to identifiability;
- diagnostics for computation and predictive checks.

Calculate truth from the generator, not by reading a similarly named fitted parameter whose definition may differ.

## 6. Define Success and Failure

Predefine tolerances based on practical use:

- maximum acceptable absolute or relative bias;
- target interval coverage band;
- maximum failure or divergence rate;
- acceptable predictive score or calibration error;
- utility, regret, or decision error tolerance;
- required stability across key scenarios.

Thresholds are context-specific. Report full metric distributions even when a threshold is used.

## 7. Choose Replication Count

For a simulated proportion `p` based on `R` independent replications, the approximate Monte Carlo standard error is:

```text
sqrt(p * (1 - p) / R)
```

Use a conservative `p = 0.5` when planning without a better value. Bias and RMSE uncertainty can be estimated from replicate-level errors or bootstrap summaries. Sequentially add replications until key simulation summaries are precise enough for the decision; do not stop because a favorable point estimate first appears.

## 8. Manage Randomness

Create a stable simulation identifier from scenario and replication. Derive separate seeds for:

- parameter generation;
- observation generation;
- missingness or measurement process;
- inference initialization and sampling.

Store seeds and metadata with every result. A rerun of one failed fit should not change all other simulations.

## 9. Manage Execution Failures

Record at least:

- generated data identifier;
- scenario and replicate;
- fit status and exception;
- wall time;
- sampler configuration;
- R-hat, ESS, MCSE, divergences, and tree-depth events;
- whether retry occurred and why;
- result artifact location.

Predefine a retry policy. Retrying only unfavorable fits can bias summaries. Keep original and retried outcomes distinguishable.

## 10. Interpret Within Scope

Conclusions are conditional on:

- scenario coverage;
- generator correctness;
- fitter version and inference settings;
- metric definitions;
- available Monte Carlo precision.

Document uncovered regimes and avoid extrapolating validation beyond them.
