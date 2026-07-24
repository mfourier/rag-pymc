---
name: deploy-and-monitor-bayesian-models
description: Prepare, deploy, evaluate, update, and govern Bayesian models in production or recurring decision workflows. Use for model and data contracts, posterior predictive artifacts, batch or online scoring, calibration and prequential evaluation, delayed-label monitoring, drift and subgroup checks, decision thresholds, retraining or posterior-update triggers, model versioning, reproducibility, rollback, incident response, and operational Bayesian model cards or runbooks.
---

# Deploy and Monitor Bayesian Models

## Purpose

Turn a validated Bayesian analysis into a traceable prediction or decision service whose inputs, uncertainty, performance, updates, and failure responses are explicit. Deployment does not authorize silent changes to data, decisions, or external systems.

## Workflow

1. **Define the operational target.** State the prediction, decision, population, horizon, latency, throughput, action owner, and loss or utility.
2. **Freeze contracts.** Version feature definitions, units, categories, missing-value policy, outcome maturity, model environment, priors, posterior artifact, predictive output schema, and decision rule. Follow [deployment-contract.md](references/deployment-contract.md).
3. **Choose the serving artifact.** Decide whether to serve posterior draws, compressed parameter draws, analytic predictive parameters, posterior predictive samples, or decision summaries. Validate numerical equivalence to the audited analysis.
4. **Separate latent and recorded predictions.** Include observation noise, new-group variation, covariate uncertainty, and measurement process according to the operational question.
5. **Build reproducible scoring.** Pin model/data versions, deterministic seed behavior where sampling is used, coordinate handling, batch semantics, and failure responses.
6. **Validate before release.** Test schema, support, missingness, category novelty, prediction invariants, calibration, interval coverage, latency, subgroup behavior, and rollback on representative and adversarial fixtures.
7. **Monitor inputs and outputs.** Track availability, range, category, missingness, covariate shift, predictive distribution shift, uncertainty, action rates, latency, and errors using [monitoring-metrics.md](references/monitoring-metrics.md).
8. **Evaluate when outcomes mature.** Use prequential or time-ordered scoring, calibration, proper scores, interval coverage, decision loss, subgroup metrics, and label-delay-aware denominators.
9. **Manage updates.** Define what can be updated, when priors or likelihoods must change, how sequential data are versioned, what validation gates apply, and when to rebuild rather than condition. Follow [update-and-rollback.md](references/update-and-rollback.md).
10. **Operate incidents and rollback.** Preserve the last known good artifact, isolate upstream data failures from model failures, record affected decisions, and communicate residual uncertainty.

Use [bayesian-model-runbook.md](assets/bayesian-model-runbook.md) to document an operational model.

## Guardrails

- Do not serve posterior parameter means as outcome predictions unless that is the defined target.
- Do not discard posterior uncertainty when the decision or interval depends on it.
- Do not compare predictions with immature labels as if missing outcomes were negatives.
- Do not interpret covariate drift as automatic model failure or lack of drift as guaranteed validity.
- Do not recalibrate, refit, or update priors silently after monitoring thresholds are crossed.
- Do not condition twice on reused data during a posterior update.
- Do not let a monitoring dashboard mutate production state without an approved response path.
- Do not expose posterior draws or model artifacts containing sensitive row-level information without privacy review.

## Prediction Scoring Utility

[score_predictions.py](scripts/score_predictions.py) evaluates long-form CSV predictions. Required columns are `outcome` and `prediction`; optional `lower`, `upper`, and `group` enable interval and subgroup summaries:

```bash
uv run python .agents/skills/deploy-and-monitor-bayesian-models/scripts/score_predictions.py \
  predictions.csv --task binary --output scores.json
```

Binary scoring reports Brier and log loss. Continuous scoring reports MAE and RMSE. Intervals report empirical coverage and mean width. Scores are descriptive for the supplied evaluation set and do not establish transportability.

## Routing

- Use `$communicate-bayesian-results` for operational model cards, stakeholder summaries, and uncertainty language.
- Use `$audit-bayesian-analysis` for pre-release and incident audits.
- Use `$develop-pymc-models` for predictive sampling, mutable data, new groups, and version-sensitive PyMC implementation.
- Use `$design-bayesian-studies` for monitoring sample size, validation collection, and value of information.
- Use `$model-imperfect-data` for delayed, censored, missing, or misclassified production outcomes.

## Output Contract

Deliver the operational target, input/output and model contracts, artifact and environment versions, validation evidence, monitoring metrics and denominators, update triggers, approval gates, rollback and incident procedures, owners, prohibited uses, and unresolved risks.
