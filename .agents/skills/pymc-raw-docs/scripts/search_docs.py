#!/usr/bin/env python3
"""Search PyMC Markdown, RST, and notebook input cells without notebook outputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path

TEXT_SUFFIXES = {".md", ".rst"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | {".ipynb"}
SCOPES = ("all", "api", "learn", "guides", "contributing", "root")


def parse_args() -> argparse.Namespace:
    """Parse command-line search options."""
    parser = argparse.ArgumentParser(
        description=(
            "Search raw PyMC docs. Notebook searches inspect Markdown and code inputs "
            "but deliberately ignore stored outputs."
        )
    )
    parser.add_argument("query", help="Literal text to find, or a regex with --regex")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("datasets/raw/source"),
        help="raw documentation root (default: datasets/raw/source)",
    )
    parser.add_argument("--scope", choices=SCOPES, default="all")
    parser.add_argument("--regex", action="store_true", help="interpret query as regex")
    parser.add_argument("--case-sensitive", action="store_true")
    parser.add_argument(
        "--max-results",
        type=int,
        default=40,
        help="maximum matching lines to emit (default: 40)",
    )
    return parser.parse_args()


def compile_pattern(args: argparse.Namespace) -> re.Pattern[str]:
    """Compile the requested literal or regular-expression pattern."""
    expression = args.query if args.regex else re.escape(args.query)
    flags = 0 if args.case_sensitive else re.IGNORECASE
    try:
        return re.compile(expression, flags)
    except re.error as exc:
        raise ValueError(f"invalid regular expression: {exc}") from exc


def in_scope(path: Path, root: Path, scope: str) -> bool:
    """Return whether a source path belongs to the selected documentation scope."""
    relative = path.relative_to(root)
    if scope == "all":
        return True
    if scope == "root":
        return len(relative.parts) == 1
    return bool(relative.parts) and relative.parts[0] == scope


def iter_paths(root: Path, scope: str) -> Iterable[Path]:
    """Yield supported documentation files in deterministic path order."""
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in SUPPORTED_SUFFIXES and in_scope(path, root, scope):
            yield path


def normalize_line(line: str) -> str:
    """Collapse whitespace so each match occupies one output line."""
    return " ".join(line.strip().split())


def search_text(path: Path, root: Path, pattern: re.Pattern[str]) -> Iterable[str]:
    """Yield matching Markdown or RST lines with source line numbers."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        print(f"warning: unable to decode {path}: {exc}", file=sys.stderr)
        return
    relative = path.relative_to(root)
    for line_number, line in enumerate(lines, start=1):
        if pattern.search(line):
            yield f"{relative}:{line_number}: {normalize_line(line)}"


def cell_lines(cell: object) -> list[str]:
    """Return normalized source lines from a supported notebook cell object."""
    if not isinstance(cell, dict):
        return []
    source = cell.get("source", [])
    if isinstance(source, str):
        return source.splitlines()
    if isinstance(source, list) and all(isinstance(item, str) for item in source):
        return "".join(source).splitlines()
    return []


def search_notebook(path: Path, root: Path, pattern: re.Pattern[str]) -> Iterable[str]:
    """Yield matches from notebook inputs without reading stored outputs."""
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"warning: unable to parse {path}: {exc}", file=sys.stderr)
        return
    cells = notebook.get("cells", [])
    if not isinstance(cells, list):
        return
    relative = path.relative_to(root)
    for cell_number, cell in enumerate(cells, start=1):
        if not isinstance(cell, dict):
            continue
        cell_type = cell.get("cell_type", "unknown")
        if cell_type not in {"markdown", "code"}:
            continue
        for line_number, line in enumerate(cell_lines(cell), start=1):
            if pattern.search(line):
                yield (
                    f"{relative}:cell={cell_number}:{cell_type}:line={line_number}: "
                    f"{normalize_line(line)}"
                )


def main() -> int:
    """Run the raw-documentation search command."""
    args = parse_args()
    if args.max_results < 1:
        print("error: --max-results must be positive", file=sys.stderr)
        return 2
    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: raw documentation root does not exist: {root}", file=sys.stderr)
        return 2
    try:
        pattern = compile_pattern(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    count = 0
    for path in iter_paths(root, args.scope):
        matches = (
            search_notebook(path, root, pattern)
            if path.suffix == ".ipynb"
            else search_text(path, root, pattern)
        )
        for match in matches:
            print(match)
            count += 1
            if count >= args.max_results:
                print(f"[result limit reached: {args.max_results}]", file=sys.stderr)
                return 0
    if count == 0:
        print("No matches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
