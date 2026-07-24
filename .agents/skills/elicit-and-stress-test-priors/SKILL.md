---
name: elicit-and-stress-test-priors
description: Elicit, encode, document, and stress-test priors for Bayesian models. Use when translating expert knowledge or regularization goals into distributions; checking marginal and joint implications in parameter and observable space; diagnosing prior-data conflict or prior-dominated inference; constructing skeptical, enthusiastic, and reference scenarios; or reporting prior sensitivity for scientific estimates, predictions, and decisions.
---

# Elicit and Stress-Test Priors

## Purpose

Build priors whose implications are interpretable, defensible, and proportionate to available information. Treat “weakly informative” as a modeling claim that must be checked, not as a neutral default.

## Workflow

1. **Fix the target and scale.** Define every parameter, unit, reference category, transformation, and feasible support. Prefer elicitation on observable or decision-relevant quantities.
2. **Classify the prior role.** Label each component as domain-informed, regularizing, structural, reference, or sensitivity-only. State which behavior it is intended to prevent or represent.
3. **Elicit defensible judgments.** Ask experts about medians, quantiles, plausible bounds, signs, orderings, rates, contrasts, and scenarios rather than abstract distribution parameters. Follow [elicitation-workflow.md](references/elicitation-workflow.md).
4. **Translate judgments.** Select distributions that respect support and geometry. Solve or approximate hyperparameters from the elicited statements using [distribution-translation.md](references/distribution-translation.md).
5. **Check marginals and dependence.** Visualize each prior, then simulate the joint prior. Inspect induced correlations, transformed parameters, hierarchical scales, and constraints.
6. **Run prior predictive checks.** Simulate outcomes before conditioning on observed data. Compare generated ranges, frequencies, group patterns, tails, and impossible events with domain knowledge.
7. **Fit and diagnose.** Verify computation before interpreting sensitivity. A prior that exposes non-identifiability or poor geometry is not automatically defective.
8. **Stress-test.** Define a small, reasoned set of alternative prior families or strengths. Compare effects on scientific contrasts, predictions, tail probabilities, and decisions—not only raw parameters.
9. **Assess conflict and influence.** Distinguish prior-data tension, prior dominance under weak likelihood information, likelihood misspecification, and implementation failure. Use [sensitivity-and-conflict.md](references/sensitivity-and-conflict.md).
10. **Document the result.** Record elicited statements, translation, predictive implications, alternatives, expert disagreements, and residual assumptions.

Use [prior-elicitation-form.md](assets/prior-elicitation-form.md) to structure an elicitation session.

## Guardrails

- Do not call a broad distribution “noninformative” without defining the parameterization and consequence.
- Do not choose a prior solely because it samples easily.
- Do not elicit on an unfamiliar transformed scale when an observable scale is available.
- Do not assess hierarchical scale priors independently of the group-level implications they induce.
- Do not tune a prior to reproduce the observed posterior and then present it as external knowledge.
- Do not treat prior-data conflict as proof that either the prior or data is wrong; investigate the full generative model.
- Preserve expert disagreement as scenarios or mixtures when consensus would erase real uncertainty.
- Separate sensitivity of computation, posterior inference, prediction, and decision.

## Prior-Predictive Constraint Utility

[assess_prior_predictive.py](scripts/assess_prior_predictive.py) summarizes CSV draws and evaluates domain constraints declared in JSON:

```bash
uv run python .agents/skills/elicit-and-stress-test-priors/scripts/assess_prior_predictive.py \
  prior_predictive.csv constraints.json --output prior-check.json
```

The utility supports hard lower/upper limits and central plausibility ranges. Constraint violations are elicitation evidence, not automatic model rejection.

## Routing

- Use `$develop-pymc-models` to implement priors, transformations, hierarchical parameterizations, and prior predictive sampling in PyMC.
- Use `$bayesian-statistics-foundations` for conceptual explanations of prior, likelihood, posterior, predictive distributions, and sensitivity.
- Use `$simulation-based-calibration` for formal SBC rank/PIT experiments.
- Use `$validate-models-by-simulation` for parameter recovery, identifiability, robustness, and misspecification scenarios.

## Output Contract

Deliver:

1. parameter and observable definitions with units;
2. prior role and knowledge source;
3. elicited probability statements;
4. chosen joint distribution and translation rationale;
5. prior predictive evidence;
6. sensitivity scenarios and affected target quantities;
7. conflict or influence assessment;
8. limitations, disagreements, and recommended follow-up.
