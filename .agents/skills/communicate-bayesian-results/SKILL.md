---
name: communicate-bayesian-results
description: Communicate Bayesian analyses accurately to technical, scientific, executive, or public audiences. Use when writing reports, result sections, decision briefs, model cards, figure narratives, uncertainty statements, diagnostic summaries, comparison tables, limitations, or reproducibility handoffs; or when revising language that confuses credible and confidence intervals, posterior and predictive uncertainty, Monte Carlo error, model uncertainty, practical relevance, or causal claims.
---

# Communicate Bayesian Results

## Purpose

Make the target, conditioning assumptions, uncertainty, evidence, and decision consequence understandable without claiming more than the design and model support.

## Workflow

1. **Identify audience and action.** Determine what the reader must understand or decide, their technical background, and the cost of misinterpretation.
2. **Lead with the target.** Define the estimand, prediction, or decision in plain language, with population, unit, horizon, and scale.
3. **State the model condition.** Explain that posterior and predictive statements are conditional on the data, priors, likelihood, and structural assumptions.
4. **Report the distribution, not only a point.** Use intervals, probabilities, predictive ranges, or expected utilities that match the target.
5. **Separate uncertainty layers.** Distinguish posterior parameter uncertainty, outcome variability, posterior predictive uncertainty, Monte Carlo error, model sensitivity, data quality, and identification uncertainty. Follow [reporting-contract.md](references/reporting-contract.md).
6. **Present diagnostics as evidence.** Report R-hat, ESS, MCSE, divergences, predictive checks, calibration, and comparison diagnostics in context. Diagnostics support reliability; they do not prove scientific truth.
7. **Connect to practical meaning.** Translate scales, show absolute as well as relative effects where relevant, compare with practical thresholds, and state decision consequences.
8. **Visualize the comparison honestly.** Use shared scales, visible uncertainty, raw or predictive context, and accessible labels according to [visualization-and-language.md](references/visualization-and-language.md).
9. **Disclose sensitivity and limitations.** Lead with assumptions that materially change conclusions. Separate “not checked,” “failed check,” and “not identifiable.”
10. **Make reproduction possible.** Link data/model versions, environment, code, seeds, artifacts, and provenance for every reported output.

Use [bayesian-analysis-report.md](assets/bayesian-analysis-report.md) for a full report and [bayesian-model-card.md](assets/bayesian-model-card.md) for a reusable model artifact.

## Guardrails

- Do not describe a credible interval as a repeated-sampling confidence interval.
- Do not say there is a posterior probability that a fixed observed datum lies in a parameter interval.
- Do not use “statistically significant” as a substitute for posterior probability, practical importance, or a decision rule.
- Do not call `P(theta > 0 | data)` the probability a hypothesis is true unless hypotheses and prior model probabilities were explicitly defined.
- Do not report more decimal precision than MCSE, measurement, and decision context support.
- Do not hide divergences, high Pareto-k values, prior sensitivity, or failed predictive checks in appendices when they affect the central claim.
- Do not imply causality from observational association or predictive accuracy.
- Do not present a model comparison rank without uncertainty and diagnostic context.

## Model Card Utility

[build_model_card.py](scripts/build_model_card.py) renders a structured JSON record into Markdown:

```bash
uv run python .agents/skills/communicate-bayesian-results/scripts/build_model_card.py \
  model-card.json --output MODEL_CARD.md
```

The utility validates core identity and use fields while preserving lists and nested mappings. It formats documentation; it does not assess truth or completeness of supplied claims.

## Routing

- Use `$bayesian-statistics-foundations` for conceptual explanation and metric interpretation.
- Use `$audit-bayesian-analysis` to establish evidence and severity before writing an audit conclusion.
- Use `$do-bayesian-causal-inference` to calibrate causal language and identification claims.
- Use `$deploy-and-monitor-bayesian-models` for operational model cards, monitoring, update, and rollback documentation.

## Output Contract

Deliver an audience-calibrated result with target definition, model and data context, posterior or predictive quantities, diagnostics, practical interpretation, sensitivity, limitations, decision implication, and reproducibility references. Ensure every probability statement has an explicit subject and conditioning context.
