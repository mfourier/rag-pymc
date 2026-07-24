# Boundary Between General Simulation Validation and Formal SBC

## Use Formal SBC When

The goal is to test calibration of a Bayesian inference algorithm or implementation under the joint generative distribution:

1. draw parameters from the prior;
2. draw data from the likelihood conditional on those parameters;
3. fit the same model to the simulated data;
4. compare the true parameter with posterior draws using ranks, randomized ranks, PIT, or ECDF diagnostics.

Questions involving rank uniformity, U-shapes, humps, skewed rank histograms, ties, discrete parameters, autocorrelated MCMC draws, thinning for SBC, prior SBC, or posterior SBC belong to `$simulation-based-calibration`.

## Use General Simulation Validation When

The goal is one or more of:

- recovery at fixed or designed parameter values;
- performance across a scenario grid not drawn from the prior;
- identifiability under particular sample sizes or designs;
- robustness under a generator different from the fitted model;
- measurement, missingness, selection, censoring, or drift stress tests;
- predictive or decision operating characteristics;
- debugging a generative or post-processing implementation.

These experiments can use bias, MAE, RMSE, coverage, calibration, utility, regret, and failure rates without claiming formal SBC calibration.

## Why the Distinction Matters

Uniform SBC ranks have a particular interpretation only under the SBC joint experiment and appropriate handling of posterior draws. A fixed-parameter recovery grid does not generally yield uniform ranks. Conversely, averaging over a broad prior in SBC can hide poor behavior in a narrow operational regime; targeted recovery studies complement SBC.

## Combined Validation Program

A mature validation program may include:

1. unit and shape tests for generator and target calculations;
2. exact-model recovery at interpretable parameter points;
3. formal prior SBC for inference calibration;
4. targeted studies in weak-identification and boundary regimes;
5. misspecification and observation-process stress tests;
6. real-data prior and posterior predictive checks;
7. held-out or prequential predictive evaluation;
8. decision and utility simulations.

Report each component with its own claim. Do not merge results into one undifferentiated “validated” label.

## Routing Examples

| Request | Route |
|---|---|
| “Can this design recover a small slope with 20 groups?” | General simulation validation |
| “Why is the SBC rank histogram U-shaped?” | Formal SBC |
| “How robust is the model to heavy-tailed residuals?” | General simulation validation |
| “How should I handle ties for a discrete SBC quantity?” | Formal SBC |
| “Does a 90% interval cover truth in a fixed scenario grid?” | General simulation validation |
| “Are posterior ranks uniform under prior-generated datasets?” | Formal SBC |
| “What happens under MNAR missingness if I fit MAR?” | General simulation validation plus imperfect-data skill |

When a study contains both components, analyze formal SBC outputs under the SBC skill and scenario recovery outputs under this skill.
