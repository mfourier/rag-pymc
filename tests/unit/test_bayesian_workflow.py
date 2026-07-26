from pathlib import Path

import numpy as np
import numpy.typing as npt
import pymc as pm  # type: ignore[import-untyped]
import pytest
import xarray as xr

from rag_pymc.bayesian_workflow import (
    AnalyticalPosterior,
    analytical_posterior,
    generate_synthetic_data,
)

SEED = 20260724
N_OBSERVATIONS = 100
TRUE_PROBABILITY = 0.65
PRIOR_ALPHA = 2.0
PRIOR_BETA = 2.0
OBSERVATION_DIM = "observation"


@pytest.fixture(scope="module")
def observations() -> np.ndarray:
    return generate_synthetic_data(
        n_observations=N_OBSERVATIONS,
        true_probability=TRUE_PROBABILITY,
        seed=SEED,
    )


@pytest.fixture(scope="module")
def model(observations: np.ndarray) -> pm.Model:
    coords = {OBSERVATION_DIM: np.arange(observations.size, dtype=np.int64)}
    with pm.Model(coords=coords) as beta_bernoulli_model:
        theta = pm.Beta("theta", alpha=PRIOR_ALPHA, beta=PRIOR_BETA)
        pm.Bernoulli("y", p=theta, observed=observations, dims=OBSERVATION_DIM)
    return beta_bernoulli_model


@pytest.fixture(scope="module")
def smoke_posterior(model: pm.Model) -> xr.DataTree:
    with model:
        posterior = pm.sample(
            chains=2,
            draws=40,
            tune=40,
            random_seed=[SEED, SEED + 1],
            cores=1,
            progressbar=False,
            compute_convergence_checks=False,
        )
        posterior = pm.sample_posterior_predictive(
            posterior,
            var_names=["y"],
            random_seed=SEED + 2,
            progressbar=False,
            extend_inferencedata=True,
        )
    assert isinstance(posterior, xr.DataTree)
    return posterior


def test_synthetic_data_are_deterministic_for_the_same_seed() -> None:
    first = generate_synthetic_data(
        n_observations=N_OBSERVATIONS,
        true_probability=TRUE_PROBABILITY,
        seed=SEED,
    )
    second = generate_synthetic_data(
        n_observations=N_OBSERVATIONS,
        true_probability=TRUE_PROBABILITY,
        seed=SEED,
    )

    np.testing.assert_array_equal(first, second)


def test_synthetic_data_have_binary_support_shape_and_stable_dtype(
    observations: np.ndarray,
) -> None:
    assert observations.shape == (N_OBSERVATIONS,)
    assert observations.dtype == np.dtype(np.int8)
    assert set(np.unique(observations)) <= {0, 1}


@pytest.mark.parametrize(
    ("n_observations", "true_probability", "seed"),
    [(0, 0.65, 1), (10, -0.1, 1), (10, 1.1, 1), (10, 0.65, -1)],
)
def test_data_generation_rejects_invalid_inputs(
    n_observations: int, true_probability: float, seed: int
) -> None:
    with pytest.raises(ValueError):
        generate_synthetic_data(
            n_observations=n_observations,
            true_probability=true_probability,
            seed=seed,
        )


@pytest.mark.parametrize("invalid", [[0, 2], [], [[0, 1]]])
def test_analytical_oracle_rejects_invalid_observations(invalid: npt.ArrayLike) -> None:
    with pytest.raises(ValueError, match="observations"):
        analytical_posterior(invalid, prior_alpha=2.0, prior_beta=2.0)


@pytest.mark.parametrize(
    ("prior_alpha", "prior_beta"),
    [(0.0, 2.0), (-1.0, 2.0), (2.0, 0.0), (2.0, float("inf"))],
)
def test_analytical_oracle_rejects_invalid_prior_parameters(
    prior_alpha: float, prior_beta: float
) -> None:
    with pytest.raises(ValueError, match="prior_"):
        analytical_posterior([0, 1], prior_alpha=prior_alpha, prior_beta=prior_beta)


def test_model_has_expected_variables_coordinate_dimension_and_finite_logp(
    model: pm.Model,
) -> None:
    assert {variable.name for variable in model.free_RVs} == {"theta"}
    assert {variable.name for variable in model.observed_RVs} == {"y"}
    assert model.named_vars_to_dims["y"] == (OBSERVATION_DIM,)
    assert model.coords[OBSERVATION_DIM] == tuple(range(N_OBSERVATIONS))
    initial_logp = model.compile_logp()(model.initial_point())
    assert np.all(np.isfinite(initial_logp))


def test_prior_predictive_has_expected_groups_dimensions_and_finite_values(
    model: pm.Model,
) -> None:
    with model:
        prior = pm.sample_prior_predictive(
            draws=25,
            var_names=["theta", "y"],
            random_seed=SEED + 1,
        )

    assert isinstance(prior, xr.DataTree)
    assert {"/prior", "/prior_predictive", "/observed_data"} <= set(prior.groups)
    theta = prior["prior"].dataset["theta"]
    replicated = prior["prior_predictive"].dataset["y"]
    assert theta.dims == ("chain", "draw")
    assert replicated.dims == ("chain", "draw", OBSERVATION_DIM)
    assert replicated.shape == (1, 25, N_OBSERVATIONS)
    assert np.all(np.isfinite(theta.values))
    assert np.all(np.isfinite(replicated.values))
    assert set(np.unique(replicated.values)) <= {0, 1}


def test_analytical_posterior_matches_exact_conjugate_calculation() -> None:
    result = analytical_posterior([1, 1, 0], prior_alpha=2.0, prior_beta=2.0)

    assert result == AnalyticalPosterior(alpha=4.0, beta=3.0, mean=4.0 / 7.0)


def test_sampling_smoke_path_returns_posterior_and_predictive_groups(
    smoke_posterior: xr.DataTree,
) -> None:
    assert isinstance(smoke_posterior, xr.DataTree)
    assert {"/posterior", "/sample_stats", "/observed_data", "/posterior_predictive"} <= set(
        smoke_posterior.groups
    )
    assert smoke_posterior["posterior"].dataset["theta"].dims == ("chain", "draw")
    replicated = smoke_posterior["posterior_predictive"].dataset["y"]
    assert replicated.dims == ("chain", "draw", OBSERVATION_DIM)
    assert replicated.shape == (2, 40, N_OBSERVATIONS)
    assert np.all(np.isfinite(replicated.values))


def test_datatree_round_trip_through_netcdf(tmp_path: Path, smoke_posterior: xr.DataTree) -> None:
    posterior_path = tmp_path / "posterior.nc"
    smoke_posterior.to_netcdf(posterior_path, engine="h5netcdf")

    with xr.open_datatree(posterior_path, engine="h5netcdf") as restored:
        assert restored.groups == smoke_posterior.groups
        np.testing.assert_allclose(
            restored["posterior"].dataset["theta"].values,
            smoke_posterior["posterior"].dataset["theta"].values,
        )
        np.testing.assert_array_equal(
            restored["posterior_predictive"].dataset["y"].values,
            smoke_posterior["posterior_predictive"].dataset["y"].values,
        )
