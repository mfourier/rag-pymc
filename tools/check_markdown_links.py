"""Fail when a local Markdown link points to a missing repository path."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

_LINK = re.compile(r"(?<!!)\[[^\]]+\]\((?P<target>[^)]+)\)")
_EXTERNAL_SCHEMES = frozenset({"http", "https", "mailto"})
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def find_missing_links(paths: tuple[Path, ...]) -> tuple[str, ...]:
    """Return stable diagnostics for local link targets that do not exist."""
    missing: list[str] = []
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in _LINK.finditer(line):
                raw_target = match.group("target").strip().strip("<>")
                parsed = urlsplit(raw_target)
                if parsed.scheme in _EXTERNAL_SCHEMES or not parsed.path:
                    continue
                target = Path(unquote(parsed.path))
                resolved = (
                    PROJECT_ROOT / target.relative_to("/")
                    if target.is_absolute()
                    else path.parent / target
                )
                if not resolved.exists():
                    relative_path = path.relative_to(PROJECT_ROOT)
                    missing.append(f"{relative_path}:{line_number}: missing {raw_target}")
    return tuple(missing)


def main() -> None:
    """Check the README and all versioned project documentation."""
    paths = (PROJECT_ROOT / "README.md", *sorted((PROJECT_ROOT / "docs").rglob("*.md")))
    missing = find_missing_links(paths)
    if missing:
        raise SystemExit("\n".join(missing))
    print(f"checked {len(paths)} Markdown files")


if __name__ == "__main__":
    main()
