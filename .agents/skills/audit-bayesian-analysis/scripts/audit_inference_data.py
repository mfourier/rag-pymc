#!/usr/bin/env python3
"""Inventory diagnostics in an ArviZ-compatible NetCDF artifact.

The output is evidence for an audit, not a model-validity certificate.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import arviz as az
from xarray import DataTree


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="NetCDF inference artifact")
    parser.add_argument("--output", default="-", help="JSON path or '-' for stdout")
    parser.add_argument(
        "--rhat-threshold",
        type=float,
        default=1.01,
        help="Operational review threshold; default: 1.01",
    )
    parser.add_argument(
        "--ess-threshold",
        type=float,
        default=400.0,
        help="Operational bulk/tail ESS review threshold; default: 400",
    )
    parser.add_argument(
        "--mcse-sd-fraction",
        type=float,
        default=0.05,
        help="Flag MCSE(mean)/posterior SD above this fraction; default: 0.05",
    )
    return parser.parse_args()


def finite_float(value: object) -> float | None:
    """Return a finite float or None for an invalid metric value."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def group_names(data: DataTree) -> list[str]:
    """Return normalized non-root DataTree group names."""
    return sorted(group.strip("/") for group in data.groups if group != "/")


def scalar_sum(group: DataTree, variable: str) -> int | None:
    """Sum a sampler-stat variable when it is available."""
    if variable not in group.data_vars:
        return None
    value = group[variable].sum().item()
    return int(value)


def posterior_inventory(data: DataTree, args: argparse.Namespace) -> dict[str, Any]:
    """Build posterior dimensions and scalar diagnostic summaries."""
    if "posterior" not in group_names(data):
        return {"available": False, "reason": "posterior group is absent"}

    posterior = data.posterior
    sizes = {str(name): int(size) for name, size in posterior.sizes.items()}
    result: dict[str, Any] = {
        "available": True,
        "sizes": sizes,
        "variables": sorted(str(name) for name in posterior.data_vars),
    }

    try:
        frame = az.summary(data, group="posterior", kind="all", round_to=None)
    except Exception as error:  # preserve a useful inventory even if summary fails
        result["summary_error"] = f"{type(error).__name__}: {error}"
        return result

    metrics = ("mean", "sd", "ess_bulk", "ess_tail", "r_hat", "mcse_mean", "mcse_sd")
    rows: list[dict[str, Any]] = []
    for index, row in frame.iterrows():
        item: dict[str, Any] = {"quantity": str(index)}
        for metric in metrics:
            item[metric] = finite_float(row[metric]) if metric in frame.columns else None

        flags: list[str] = []
        r_hat = item.get("r_hat")
        if r_hat is not None and r_hat > args.rhat_threshold:
            flags.append("r_hat_above_operational_threshold")
        for metric in ("ess_bulk", "ess_tail"):
            value = item.get(metric)
            if value is not None and value < args.ess_threshold:
                flags.append(f"{metric}_below_operational_threshold")
        sd = item.get("sd")
        mcse_mean = item.get("mcse_mean")
        if sd is not None and sd > 0 and mcse_mean is not None:
            item["mcse_mean_sd_fraction"] = mcse_mean / sd
            if item["mcse_mean_sd_fraction"] > args.mcse_sd_fraction:
                flags.append("mcse_mean_large_relative_to_posterior_sd")
        else:
            item["mcse_mean_sd_fraction"] = None
        item["flags"] = flags
        rows.append(item)

    result["summary"] = rows
    result["flagged_quantity_count"] = sum(bool(item["flags"]) for item in rows)
    return result


def sampler_inventory(data: DataTree) -> dict[str, Any]:
    """Build an inventory of sampler statistics and event counts."""
    if "sample_stats" not in group_names(data):
        return {"available": False, "reason": "sample_stats group is absent"}

    stats = data.sample_stats
    variables = sorted(str(name) for name in stats.data_vars)
    result: dict[str, Any] = {"available": True, "variables": variables}

    for canonical, candidates in {
        "divergences": ("diverging", "divergences"),
        "reached_max_treedepth": ("reached_max_treedepth",),
    }.items():
        result[canonical] = None
        for candidate in candidates:
            value = scalar_sum(stats, candidate)
            if value is not None:
                result[canonical] = value
                result[f"{canonical}_source"] = candidate
                break

    if "tree_depth" in stats.data_vars:
        result["maximum_observed_tree_depth"] = int(stats["tree_depth"].max().item())
    return result


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    """Load the artifact and assemble its diagnostic report."""
    data = az.from_netcdf(args.input)
    groups = group_names(data)
    return {
        "artifact": str(args.input.resolve()),
        "groups": groups,
        "operational_thresholds": {
            "r_hat": args.rhat_threshold,
            "ess_bulk_and_tail": args.ess_threshold,
            "mcse_mean_as_fraction_of_posterior_sd": args.mcse_sd_fraction,
        },
        "posterior": posterior_inventory(data, args),
        "sampler": sampler_inventory(data),
        "limitations": [
            "Threshold flags are review prompts, not pass/fail criteria.",
            (
                "The inventory does not assess model identification, prior plausibility, "
                "predictive adequacy, causal assumptions, or fitness for use."
            ),
            "Missing diagnostics may reflect an incomplete artifact rather than a failed analysis.",
        ],
    }


def main() -> int:
    """Run the command-line diagnostic inventory."""
    args = parse_args()
    if args.rhat_threshold <= 1:
        raise SystemExit("--rhat-threshold must be greater than 1")
    if args.ess_threshold <= 0 or args.mcse_sd_fraction <= 0:
        raise SystemExit("ESS and MCSE thresholds must be positive")

    report = build_report(args)
    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    if args.output == "-":
        print(rendered)
    else:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
