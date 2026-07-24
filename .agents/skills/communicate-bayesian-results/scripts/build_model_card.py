#!/usr/bin/env python3
"""Render a structured JSON Bayesian model card as Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED = ("title", "version", "status", "owners", "intended_use", "target")
IDENTITY_ORDER = ("title", "version", "status", "owners")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Structured JSON model-card record")
    parser.add_argument("--output", default="-", help="Markdown path or '-' for stdout")
    return parser.parse_args()


def heading(key: str) -> str:
    """Convert a JSON key into a human-readable Markdown heading."""
    return key.replace("_", " ").strip().title()


def scalar(value: object) -> str:
    """Render a scalar-like JSON value as text."""
    if value is None:
        return "Not provided"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value).strip() or "Not provided"


def render_value(value: object, level: int) -> list[str]:
    """Render a nested JSON value as Markdown lines."""
    if isinstance(value, dict):
        lines: list[str] = []
        for key, nested in value.items():
            lines.extend([f"{'#' * level} {heading(str(key))}", ""])
            lines.extend(render_value(nested, level + 1))
        return lines
    if isinstance(value, list):
        if not value:
            return ["Not provided", ""]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                rendered = render_value(item, level + 1)
                first = rendered[0] if rendered else "Not provided"
                lines.append(f"- {first}")
                lines.extend(f"  {line}" if line else "" for line in rendered[1:])
            else:
                lines.append(f"- {scalar(item)}")
        return [*lines, ""]
    return [scalar(value), ""]


def render(card: dict[str, Any]) -> str:
    """Render a validated model-card mapping as Markdown."""
    title = scalar(card["title"])
    lines = [f"# {title}", "", "## Identity", ""]
    for key in IDENTITY_ORDER[1:]:
        value = card[key]
        if isinstance(value, list):
            rendered = ", ".join(scalar(item) for item in value) or "Not provided"
        else:
            rendered = scalar(value)
        lines.append(f"- **{heading(key)}:** {rendered}")
    lines.append("")

    ordered_keys = ["intended_use", "target"]
    ordered_keys.extend(key for key in card if key not in set(IDENTITY_ORDER + tuple(ordered_keys)))
    for key in ordered_keys:
        lines.extend([f"## {heading(key)}", ""])
        lines.extend(render_value(card[key], 3))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    """Run the JSON-to-Markdown model-card command."""
    args = parse_args()
    card = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(card, dict):
        raise SystemExit("model card JSON must be an object")
    missing = [key for key in REQUIRED if key not in card]
    if missing:
        raise SystemExit(f"missing required model-card fields: {missing}")
    if not isinstance(card["owners"], list) or not card["owners"]:
        raise SystemExit("owners must be a non-empty JSON array")

    rendered = render(card)
    if args.output == "-":
        print(rendered, end="")
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
