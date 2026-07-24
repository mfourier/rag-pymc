#!/usr/bin/env python3
"""Score binary or continuous predictions from a CSV evaluation cohort."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean
from typing import Any

REQUIRED = {"outcome", "prediction"}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Prediction CSV")
    parser.add_argument("--task", choices=("binary", "continuous"), required=True)
    parser.add_argument("--output", default="-", help="JSON path or '-' for stdout")
    parser.add_argument(
        "--probability-clip",
        type=float,
        default=1e-15,
        help="Numerical clipping used only for binary log loss; default: 1e-15",
    )
    return parser.parse_args()


def finite(raw: str, name: str) -> float:
    """Parse a required finite numeric CSV field."""
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError(f"{name} is not finite")
    return value


def score_rows(rows: list[dict[str, str]], task: str, clip: float) -> dict[str, Any]:
    """Score one complete evaluation cohort or subgroup."""
    squared_errors: list[float] = []
    absolute_errors: list[float] = []
    log_losses: list[float] = []
    coverages: list[float] = []
    widths: list[float] = []
    invalid_reasons: dict[str, int] = defaultdict(int)

    for row in rows:
        try:
            outcome = finite(row["outcome"], "outcome")
            prediction = finite(row["prediction"], "prediction")
            row_log_loss: float | None = None
            if task == "binary":
                if outcome not in (0.0, 1.0):
                    raise ValueError("binary outcome must be 0 or 1")
                if not 0 <= prediction <= 1:
                    raise ValueError("binary prediction must be in [0, 1]")
                clipped = min(max(prediction, clip), 1 - clip)
                row_log_loss = -(
                    outcome * math.log(clipped) + (1 - outcome) * math.log(1 - clipped)
                )

            error = prediction - outcome
            raw_lower = row.get("lower", "").strip()
            raw_upper = row.get("upper", "").strip()
            if bool(raw_lower) != bool(raw_upper):
                raise ValueError("lower and upper must be provided together")
            interval: tuple[float, float] | None = None
            if raw_lower:
                lower = finite(raw_lower, "lower")
                upper = finite(raw_upper, "upper")
                if lower > upper:
                    raise ValueError("lower exceeds upper")
                interval = (lower, upper)
        except (TypeError, ValueError, KeyError) as error:
            invalid_reasons[str(error)] += 1
            continue

        squared_errors.append(error**2)
        absolute_errors.append(abs(error))
        if row_log_loss is not None:
            log_losses.append(row_log_loss)
        if interval is not None:
            lower, upper = interval
            coverages.append(1.0 if lower <= outcome <= upper else 0.0)
            widths.append(upper - lower)

    valid = len(squared_errors)
    result: dict[str, Any] = {
        "attempted": len(rows),
        "valid": valid,
        "invalid": len(rows) - valid,
        "invalid_reasons": dict(sorted(invalid_reasons.items())),
    }
    if not valid:
        result["metrics"] = None
        return result

    metrics: dict[str, Any]
    if task == "binary":
        metrics = {
            "brier_score": fmean(squared_errors),
            "log_loss": fmean(log_losses),
            "log_loss_probability_clip": clip,
        }
    else:
        metrics = {
            "mae": fmean(absolute_errors),
            "rmse": math.sqrt(fmean(squared_errors)),
        }
    metrics["interval_observations"] = len(coverages)
    metrics["empirical_interval_coverage"] = fmean(coverages) if coverages else None
    metrics["mean_interval_width"] = fmean(widths) if widths else None
    result["metrics"] = metrics
    return result


def main() -> int:
    """Run the prediction-scoring command."""
    args = parse_args()
    if not 0 < args.probability_clip < 0.5:
        raise SystemExit("--probability-clip must be between 0 and 0.5")

    rows: list[dict[str, str]] = []
    with args.input.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - columns)
        if missing:
            raise SystemExit(f"missing required CSV columns: {missing}")
        rows = list(reader)

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    if rows and "group" in rows[0]:
        for row in rows:
            groups[row.get("group", "") or "(missing group)"].append(row)

    report = {
        "input": str(args.input.resolve()),
        "task": args.task,
        "overall": score_rows(rows, args.task, args.probability_clip),
        "groups": [
            {"group": group, **score_rows(group_rows, args.task, args.probability_clip)}
            for group, group_rows in sorted(groups.items())
        ],
        "interpretation_note": (
            "Scores describe this evaluation cohort and its outcome-maturity rules. They do not "
            "by themselves establish calibration in another population or time period."
        ),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    if args.output == "-":
        print(rendered)
    else:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
