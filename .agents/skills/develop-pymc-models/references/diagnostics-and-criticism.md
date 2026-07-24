# Diagnostics and Model Criticism

Use diagnostics to answer specific computational and predictive questions. No single number proves convergence, calibration, identification, or scientific validity.

## Sampling diagnostics

Inspect at least the following for inferential runs:

| Diagnostic | Question it informs | Important limitation |
| --- | --- | --- |
| Rank-normalized split R-hat | Do split chains show compatible rank behavior? | A value near one does not prove exploration of every mode or model correctness. |
| Bulk ESS | How much information is available for central posterior summaries? | It is quantity- and chain-dependent, not an independent sample count in a literal sense. |
| Tail ESS | How much information is available for tails and quantiles? | Central summaries may look stable while tails remain poorly estimated. |
| MCSE | How much Monte Carlo uncertainty affects a reported estimate? | It does not include model or data uncertainty. |
| Divergences | Did Hamiltonian integration fail in regions of posterior geometry? | Their absence alone does not establish convergence. |
| Tree depth | Did trajectories repeatedly hit the configured depth limit? | Raising the limit can increase work without fixing geometry. |
| Energy diagnostics | Does the kinetic-energy behavior suggest poor exploration? | Interpret with other diagnostics and model structure. |
| Trace and rank plots | Do chains mix, drift, stick, or occupy different regions? | Visual checks are necessary but not sufficient. |

Use ArviZ summary and plotting functions that exist in the pinned ArviZ 1.2.0 runtime. Verify signatures locally because the online ArviZ API may move diagnostics into more specialized functions.

Choose numerical acceptability based on the required precision and decision. If the result depends on a threshold, report the threshold, the affected variables, and why it is adequate for the target estimand.

## Divergence workflow

When divergences occur:

1. Confirm they are post-tuning and count them by chain.
2. Locate divergent draws in parameter pairs and transformed quantities.
3. Identify likely funnels, boundaries, strong correlations, weak identification, or extreme curvature.
4. Check whether priors and likelihood create that geometry for substantive reasons.
5. Try a defensible reparameterization, rescaling, or more informative prior.
6. Re-run and compare all diagnostics, not only divergence count.
7. Increase `target_accept` when smaller integration steps are a justified mitigation, while acknowledging that this can cost computation and may not fix the geometry.

Longer chains alone do not repair biased exploration caused by unresolved divergences. Non-centering is a common candidate for weakly informed hierarchical effects, but it is not universally preferable.

## Posterior predictive criticism

Posterior predictive checks compare observed data with replicated data generated under the fitted model. Select discrepancies before looking only for plots that flatter the model.

Check features relevant to the application, such as:

- location, dispersion, skewness, and tails;
- zeros, extremes, and censoring patterns;
- subgroup distributions and partial pooling behavior;
- temporal or spatial autocorrelation;
- calibration of decision-relevant events;
- residual structure against predictors or fitted values.

Label conclusions narrowly. For example, matching the marginal outcome histogram does not establish that subgroup dependence or causal structure is adequate.

Prior predictive checks ask whether the prior generative model produces plausible data. Posterior predictive checks ask whether the fitted model can reproduce selected observable features. Simulation-based calibration asks whether an inference procedure is calibrated across repeated simulations. Keep these roles distinct.

## Predictive model comparison

Use pointwise log likelihood and LOO/ELPD when models target the same predictive units and outcome. Inspect Pareto diagnostics and the uncertainty of differences. Avoid treating the largest estimated ELPD as a definitive scientific winner when differences are uncertain or the predictive target is misaligned with the decision.

Cross-validation evaluates predictive behavior under a data-splitting scheme. It does not validate priors, identify causal effects, or prove that the likelihood represents the data-generating process.

## Escalation to SBC

Invoke `$simulation-based-calibration` when the question concerns repeated-simulation calibration of the posterior algorithm or implementation, rank uniformity, PIT/ECDF behavior, ties, discrete parameters, MCMC autocorrelation, thinning for ranks, or posterior SBC conditional on observed data. Preserve that skill's paper-level assumptions and limitations.

## Reporting template

Report diagnostics as evidence, not ceremony:

1. sampler, chains, tuning, draws, seed, and backend;
2. worst or relevant R-hat, ESS, and MCSE values with affected variables;
3. divergence and tree-depth counts and locations;
4. predictive discrepancies checked and failures observed;
5. sensitivity analyses and changes in substantive conclusions;
6. unresolved limitations and the next diagnostic action.
