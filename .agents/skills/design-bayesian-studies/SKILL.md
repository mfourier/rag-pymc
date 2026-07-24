---
name: design-bayesian-studies
description: Design prospective Bayesian studies using assurance, expected precision, predictive performance, expected utility, value of information, and simulation-based operating characteristics. Use for sample-size and allocation decisions, hierarchical or cluster designs, validation subsamples, adaptive or sequential designs, stopping rules, multiplicity-aware decisions, data-collection prioritization, or comparing candidate study designs under prior uncertainty.
---

# Design Bayesian Studies

## Purpose

Choose a data-collection design that is adequate for a stated inferential, predictive, or decision objective before observing the study outcomes. Integrate over uncertainty in plausible data-generating states rather than designing around a single favorable effect.

## Workflow

1. **Define the use.** State the estimand, prediction, or action; target population; time horizon; practical consequence; and constraints.
2. **Choose a design criterion.** Use expected precision, posterior probability, interval exclusion, predictive performance, assurance, expected utility, regret, or value of information according to the real objective. See [assurance-and-precision.md](references/assurance-and-precision.md).
3. **Specify design-stage uncertainty.** Define distributions or scenarios for effects, heterogeneity, prevalence, variance, missingness, compliance, measurement error, recruitment, and cost. Keep design priors distinct from analysis priors when they play different roles.
4. **Enumerate candidate designs.** Include sample size, cluster and group allocation, measurement schedule, validation subsample, follow-up, adaptive options, and operational constraints.
5. **Simulate the complete workflow.** Generate latent states and observed data, fit or approximate the planned analysis, calculate target quantities, apply the decision or stopping rule, and record cost and failures. Follow [design-workflow.md](references/design-workflow.md).
6. **Estimate operating characteristics.** Report assurance or success probability, interval width, calibration, bias where relevant, action rates, utility, regret, duration, cost, and computational failure with Monte Carlo uncertainty.
7. **Evaluate sequential behavior.** Simulate all looks, adaptations, delayed outcomes, and maximum sample size. Use [decision-and-sequential-design.md](references/decision-and-sequential-design.md).
8. **Stress-test.** Vary priors, recruitment, dropout, effect heterogeneity, measurement quality, model misspecification, and implementation constraints.
9. **Select transparently.** Compare designs using a predeclared criterion and resource constraints. Identify near-optimal alternatives and sensitivity of the ranking.
10. **Lock the protocol.** Version the generator, analysis model, decision rule, simulation seeds, adaptations, thresholds, and reporting plan.

Use [study-design-protocol.md](assets/study-design-protocol.md) as the design record.

## Guardrails

- Do not call assurance “power” without stating the design-stage distribution being averaged over.
- Do not choose sample size using only one assumed effect when substantive uncertainty is central.
- Do not optimize posterior precision for a parameter that is not the study estimand.
- Do not reuse the analysis prior as a design prior without checking whether that role is appropriate.
- Do not evaluate an adaptive rule at only the final sample size; simulate its full path and stopping behavior.
- Do not ignore failed fits, recruitment shortfalls, delayed outcomes, or missingness in operating characteristics.
- Do not introduce a stopping threshold after inspecting favorable simulations and report it as prespecified.
- Do not equate a high probability of a posterior threshold with high expected decision value.

## Simulation Summary Utility

[summarize_design_simulations.py](scripts/summarize_design_simulations.py) summarizes a CSV with required `design`, `replicate`, and `success` columns and optional `utility`, `cost`, `interval_width`, and `status`:

```bash
uv run python .agents/skills/design-bayesian-studies/scripts/summarize_design_simulations.py \
  design-results.csv --output design-summary.json
```

The script reports design-level success, utility, cost, precision, and failure metrics with Monte Carlo standard errors where available.

## Routing

- Use `$elicit-and-stress-test-priors` for design-stage distributions and analysis priors.
- Use `$validate-models-by-simulation` for recovery, identifiability, and robustness not centered on prospective design selection.
- Use `$model-imperfect-data` for validation subsamples, nonresponse, measurement error, censoring, and informative follow-up.
- Use `$develop-pymc-models` for executable PyMC analysis and simulation code.
- Use `$do-bayesian-causal-inference` when the design targets a causal estimand or requires randomization, interference, or transport assumptions.

## Output Contract

Deliver the objective and criterion, design-stage uncertainty, candidate designs, complete simulation protocol, operating characteristics with Monte Carlo uncertainty, sequential and multiplicity rules, cost or utility assumptions, sensitivity analysis, selected design with rationale, and residual risks.
