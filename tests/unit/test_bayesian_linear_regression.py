import ast
import json
from pathlib import Path

import numpy as np
import pymc as pm  # type: ignore[import-untyped]
import pytest
import xarray as xr

PROJECT_ROOT = Path(__file__).parents[2]
NOTEBOOK_PATH = (
    PROJECT_ROOT / "examples" / "bayesian_workflow" / "bayesian_workflow_linear_regression.ipynb"
)

SEED = 20260726
N_OBSERVATIONS = 16
INTERCEPT_TRUE = 1.0
SLOPE_TRUE = 2.0
SIGMA_TRUE = 0.75
PRIOR_INTERCEPT_MEAN = 0.5
PRIOR_INTERCEPT_SD = 2.5
PRIOR_SLOPE_MEAN = 1.5
PRIOR_SLOPE_SD = 2.0
PRIOR_SIGMA_SD = 1.0
OBSERVATION_DIM = "observation"


@pytest.fixture(scope="module")
def constructed_data() -> tuple[np.ndarray, np.ndarray]:
    predictor = np.linspace(-1.5, 1.5, N_OBSERVATIONS)
    true_mean = INTERCEPT_TRUE + SLOPE_TRUE * predictor
    generator = np.random.default_rng(SEED)
    observations = generator.normal(loc=true_mean, scale=SIGMA_TRUE)
    return predictor, observations


@pytest.fixture(scope="module")
def model(constructed_data: tuple[np.ndarray, np.ndarray]) -> pm.Model:
    predictor, observations = constructed_data
    coords = {OBSERVATION_DIM: np.arange(N_OBSERVATIONS, dtype=np.int64)}
    with pm.Model(coords=coords) as linear_model:
        intercept = pm.Normal("intercept", mu=PRIOR_INTERCEPT_MEAN, sigma=PRIOR_INTERCEPT_SD)
        slope = pm.Normal("slope", mu=PRIOR_SLOPE_MEAN, sigma=PRIOR_SLOPE_SD)
        sigma = pm.HalfNormal("sigma", sigma=PRIOR_SIGMA_SD)
        mu = pm.Deterministic("mu", intercept + slope * predictor, dims=OBSERVATION_DIM)
        pm.Normal(
            "y",
            mu=mu,
            sigma=sigma,
            observed=observations,
            dims=OBSERVATION_DIM,
        )
    return linear_model


@pytest.fixture(scope="module")
def smoke_posterior(model: pm.Model) -> xr.DataTree:
    with model:
        posterior = pm.sample(
            chains=2,
            draws=30,
            tune=30,
            random_seed=[SEED + 10, SEED + 11],
            cores=1,
            progressbar=False,
            compute_convergence_checks=False,
        )
        posterior = pm.sample_posterior_predictive(
            posterior,
            var_names=["y"],
            random_seed=SEED + 20,
            progressbar=False,
            extend_inferencedata=True,
        )
    assert isinstance(posterior, xr.DataTree)
    return posterior


def test_constructed_data_are_deterministic_finite_and_centered(
    constructed_data: tuple[np.ndarray, np.ndarray],
) -> None:
    predictor, observations = constructed_data
    second_generator = np.random.default_rng(SEED)
    second = second_generator.normal(
        loc=INTERCEPT_TRUE + SLOPE_TRUE * predictor,
        scale=SIGMA_TRUE,
    )

    np.testing.assert_array_equal(observations, second)
    assert predictor.shape == observations.shape == (N_OBSERVATIONS,)
    assert predictor.mean() == pytest.approx(0.0, abs=1e-15)
    assert (predictor.min(), predictor.max()) == (-1.5, 1.5)
    assert np.all(np.isfinite(observations))


def test_linear_model_has_expected_graph_dimensions_and_finite_initial_logp(
    model: pm.Model,
) -> None:
    assert {variable.name for variable in model.free_RVs} == {
        "intercept",
        "slope",
        "sigma",
    }
    assert {variable.name for variable in model.deterministics} == {"mu"}
    assert {variable.name for variable in model.observed_RVs} == {"y"}
    assert model.named_vars_to_dims["mu"] == (OBSERVATION_DIM,)
    assert model.named_vars_to_dims["y"] == (OBSERVATION_DIM,)
    assert model.coords[OBSERVATION_DIM] == tuple(range(N_OBSERVATIONS))
    initial_logp = model.compile_logp()(model.initial_point())
    assert np.all(np.isfinite(initial_logp))


def test_linear_model_encodes_requested_prior_locations_and_scales(model: pm.Model) -> None:
    intercept_mode_logp = float(pm.logp(model["intercept"], PRIOR_INTERCEPT_MEAN).eval())
    slope_mode_logp = float(pm.logp(model["slope"], PRIOR_SLOPE_MEAN).eval())
    sigma_mode_logp = float(pm.logp(model["sigma"], 0.0).eval())

    assert intercept_mode_logp == pytest.approx(
        -np.log(PRIOR_INTERCEPT_SD) - 0.5 * np.log(2 * np.pi)
    )
    assert slope_mode_logp == pytest.approx(-np.log(PRIOR_SLOPE_SD) - 0.5 * np.log(2 * np.pi))
    assert sigma_mode_logp == pytest.approx(0.5 * np.log(2 / np.pi) - np.log(PRIOR_SIGMA_SD))


def test_prior_predictive_has_expected_groups_dimensions_and_support(
    model: pm.Model,
) -> None:
    with model:
        prior = pm.sample_prior_predictive(
            draws=25,
            var_names=["intercept", "slope", "sigma", "mu", "y"],
            random_seed=SEED + 1,
        )

    assert isinstance(prior, xr.DataTree)
    assert {"/prior", "/prior_predictive", "/observed_data"} <= set(prior.groups)
    assert prior["prior"].dataset["intercept"].dims == ("chain", "draw")
    assert prior["prior"].dataset["mu"].dims == (
        "chain",
        "draw",
        OBSERVATION_DIM,
    )
    replicated = prior["prior_predictive"].dataset["y"]
    assert replicated.dims == ("chain", "draw", OBSERVATION_DIM)
    assert replicated.shape == (1, 25, N_OBSERVATIONS)
    assert np.all(np.isfinite(replicated.values))
    assert np.all(prior["prior"].dataset["sigma"].values > 0.0)


def test_sampling_smoke_path_returns_expected_finite_groups(
    smoke_posterior: xr.DataTree,
) -> None:
    assert {"/posterior", "/sample_stats", "/observed_data", "/posterior_predictive"} <= set(
        smoke_posterior.groups
    )
    for parameter in ("intercept", "slope", "sigma"):
        values = smoke_posterior["posterior"].dataset[parameter]
        assert values.dims == ("chain", "draw")
        assert np.all(np.isfinite(values))
    mu = smoke_posterior["posterior"].dataset["mu"]
    replicated = smoke_posterior["posterior_predictive"].dataset["y"]
    assert mu.dims == replicated.dims == ("chain", "draw", OBSERVATION_DIM)
    assert mu.shape == replicated.shape == (2, 30, N_OBSERVATIONS)
    assert np.all(np.isfinite(replicated))


def test_joint_posterior_parameter_matrix_is_finite_symmetric_and_complete(
    smoke_posterior: xr.DataTree,
) -> None:
    posterior = smoke_posterior["posterior"].dataset
    parameter_names = ("intercept", "slope", "sigma")
    joint_draw_matrix = np.column_stack(
        [posterior[parameter].values.ravel() for parameter in parameter_names]
    )
    correlation_matrix = np.corrcoef(joint_draw_matrix, rowvar=False)

    assert joint_draw_matrix.shape == (2 * 30, len(parameter_names))
    assert np.all(np.isfinite(joint_draw_matrix))
    assert correlation_matrix.shape == (len(parameter_names), len(parameter_names))
    assert np.all(np.isfinite(correlation_matrix))
    np.testing.assert_allclose(correlation_matrix, correlation_matrix.T)
    np.testing.assert_allclose(np.diag(correlation_matrix), np.ones(len(parameter_names)))


def test_linear_regression_datatree_round_trip(
    tmp_path: Path, smoke_posterior: xr.DataTree
) -> None:
    posterior_path = tmp_path / "linear-regression-posterior.nc"
    smoke_posterior.to_netcdf(posterior_path, engine="h5netcdf")

    with xr.open_datatree(posterior_path, engine="h5netcdf") as restored:
        assert restored.groups == smoke_posterior.groups
        np.testing.assert_allclose(
            restored["posterior"].dataset["slope"].values,
            smoke_posterior["posterior"].dataset["slope"].values,
        )
        np.testing.assert_array_equal(
            restored["posterior_predictive"].dataset["y"].values,
            smoke_posterior["posterior_predictive"].dataset["y"].values,
        )


def test_linear_regression_notebook_code_cells_parse() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell["source"]
            ast.parse("".join(cell["source"]), filename=cell["id"])


def test_linear_regression_is_the_only_workflow_example_notebook() -> None:
    notebook_names = sorted(path.name for path in NOTEBOOK_PATH.parent.glob("*.ipynb"))

    assert notebook_names == [NOTEBOOK_PATH.name]


def test_linear_regression_notebook_exposes_workflow_operations() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])

    for expected in (
        "Graphical_Bayesian_Workflow.md",
        "N_OBSERVATIONS = 16",
        "with $n=16$",
        r"\mathcal D=\{(x_i,y_i)\}_{i=1}^{16}",
        "Workflow: **Prior predictive check**",
        "Workflow: **Fit the model**",
        "Workflow: **Validate computation**",
        "Workflow: **Posterior predictive check**",
        "intercept = pm.Normal(",
        'pm.Normal("slope"',
        'pm.HalfNormal("sigma"',
        "PRIOR_INTERCEPT_MEAN = 0.5",
        "PRIOR_INTERCEPT_SD = 2.5",
        "PRIOR_SLOPE_MEAN = 1.5",
        "PRIOR_SLOPE_SD = 2.0",
        "PRIOR_SIGMA_SD = 1.0",
        "INTERVAL_PROBABILITY = 0.94",
        "INTERVAL_LOWER_QUANTILE = 0.03",
        "INTERVAL_UPPER_QUANTILE = 0.97",
        'pm.Deterministic("mu"',
        "Joint likelihood in three-dimensional parameter space",
        "predictor_sum_of_squares",
        "likelihood_intercept_mle",
        "likelihood_slope_mle",
        "likelihood_sigma_mle",
        "joint_log_likelihood",
        "relative_likelihood",
        "LIKELIHOOD_VISIBILITY_CUTOFF",
        "sigma_grid = likelihood_sigma_mle * np.linspace(0.25, 3.0, 56)",
        'projection="3d"',
        "computed_zorder=False",
        r"Relative likelihood $L/L_{\max}$",
        "Gaussian MLE",
        "likelihood_volume_summary",
        "pm.sample_prior_predictive(",
        "prior_mu_quantiles",
        "prior_predictive_quantiles",
        r"94% prior predictive interval for $y^{\mathrm{rep}}$",
        r"94% prior interval for mean $\mu(x)$",
        r"Prior median of the conditional mean $\mu(x)$",
        "Prior predictive implications before observing y",
        "Joint prior distribution in parameter space",
        'prior_predictive["prior"].dataset',
        "prior_relative_joint_density",
        "prior_joint_axis_limits",
        "Joint prior density mode",
        r"Relative joint prior density $p(\theta)/p_{\max}$",
        "prior_joint_summary",
        "np.linalg.lstsq(",
        "pm.sample(",
        "pm.sample_posterior_predictive(",
        "az.rhat(",
        "az.ess(",
        "az.mcse(",
        "az.bfmi(",
        "Bayesian updating: prior and posterior parameter distributions",
        r"Prior $p({symbol})$",
        r"Posterior $p({symbol}\mid x,y)$",
        "Joint posterior geometry of intercept, slope, and residual scale",
        "joint_parameter_pairs",
        "joint_correlation_matrix",
        "posterior_joint_geometry",
        "Bayes' rule in joint parameter space",
        "comparison_axis_limits",
        "Likelihood/posterior zoom window",
        "posterior_log_kernel",
        "posterior_relative_kernel",
        "posterior_inside_comparison_window.all()",
        "posterior_draws_outside_shared_window",
        "Joint Bayesian update",
        "joint_bayes_comparison_summary",
        "Posterior predictive check at the fixed observed inputs",
        r"Posterior median of the conditional mean $\mu(x)$",
        r"Observed data $y$",
        r"94% posterior predictive interval for $y^{\mathrm{rep}}$",
        "posterior.to_netcdf(",
        "xr.open_datatree(",
    ):
        assert expected in source

    for removed in (
        "Likelihood as a function of the parameters",
        "gaussian_log_likelihood",
        "intercept_log_likelihood",
        "slope_log_likelihood",
        "sigma_log_likelihood",
        "Conditional slice maximum",
        "Likelihood in observable space",
        "likelihood_indices",
        "conditional_density",
        "Gaussian observation model at three fixed inputs",
        "Prior predictive outcomes",
        "Pooled prior-predictive responses",
        '"response_q01"',
        '"response_q05"',
        '"response_q95"',
        '"response_q99"',
        "Posterior predictive criticism",
        "ppc_summary",
        "observed_rmse",
        "replicated_rmse",
        "observed_max_abs",
        "replicated_max_abs",
        "tail_area_rep_ge_obs",
    ):
        assert removed not in source
