"""Snapshot selected PyMC code and notebooks from an exact local Git tag."""

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

LIBRARY_VERSION = "6.1.0"
RELEASE_TAG = "v6.1.0"
EXPECTED_COMMIT = "56384e5afed6d1ad122e19b1bf3a7885fc38e5e5"
UPSTREAM_URL = "https://github.com/pymc-devs/pymc"


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """One upstream file and public symbol selected for the corpus."""

    source_path: str
    api_symbol: str

    @property
    def manifest_name(self) -> str:
        """Return a filesystem-safe manifest name preserving symbol identity."""
        return f"{self.api_symbol}.json"


SOURCES = (
    SourceSpec("pymc/sampling/mcmc.py", "pymc.sample"),
    SourceSpec("pymc/data.py", "pymc.Data"),
    SourceSpec("pymc/model/core.py", "pymc.model.core.set_data"),
    SourceSpec(
        "pymc/sampling/forward.py",
        "pymc.sample_posterior_predictive",
    ),
)

NOTEBOOKS = (
    "docs/source/learn/core_notebooks/dimensionality.ipynb",
    "docs/source/learn/core_notebooks/pymc_pytensor.ipynb",
    "docs/source/learn/core_notebooks/model_comparison.ipynb",
)


def _git(repository: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def _existing_downloaded_at(manifest_path: Path) -> str | None:
    if not manifest_path.exists():
        return None
    value: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"existing manifest is not an object: {manifest_path}")
    downloaded_at = value.get("downloaded_at")
    if not isinstance(downloaded_at, str):
        raise RuntimeError(f"existing manifest has no downloaded_at: {manifest_path}")
    return downloaded_at


def snapshot(repository: Path, project_root: Path) -> None:
    """Write exact source fixtures and content-addressed manifests."""
    commit = _git(repository, "rev-parse", f"{RELEASE_TAG}^{{}}").decode().strip()
    if commit != EXPECTED_COMMIT:
        raise RuntimeError(f"{RELEASE_TAG} resolved to {commit}, expected {EXPECTED_COMMIT}")

    fixture_root = project_root / "datasets/fixtures/pymc" / LIBRARY_VERSION / "repository"
    manifest_root = project_root / "datasets/raw/manifests/pymc" / LIBRARY_VERSION / "repository"
    acquisition_time = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    for spec in SOURCES:
        source = _git(repository, "show", f"{RELEASE_TAG}:{spec.source_path}")
        fixture_path = fixture_root / spec.source_path
        manifest_path = manifest_root / spec.manifest_name
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_bytes(source)

        downloaded_at = _existing_downloaded_at(manifest_path) or acquisition_time
        last_modified = (
            _git(
                repository,
                "log",
                "-1",
                "--format=%cI",
                RELEASE_TAG,
                "--",
                spec.source_path,
            )
            .decode()
            .strip()
        )
        manifest = {
            "manifest_version": "1",
            "source_id": (f"pymc-{LIBRARY_VERSION}-repository-code-{spec.api_symbol}"),
            "library": "pymc",
            "library_version": LIBRARY_VERSION,
            "source_type": "repository_code",
            "source_url": f"{UPSTREAM_URL}/blob/{RELEASE_TAG}/{spec.source_path}",
            "release_tag": RELEASE_TAG,
            "release_url": f"{UPSTREAM_URL}/releases/tag/{RELEASE_TAG}",
            "source_commit": commit,
            "source_last_modified_at": last_modified,
            "downloaded_at": downloaded_at,
            "content_hash": sha256(source).hexdigest(),
            "media_type": "text/x-python",
            "expected_api_symbol": spec.api_symbol,
            "source_path": spec.source_path,
            "license_name": "Apache-2.0",
            "license_url": f"{UPSTREAM_URL}/blob/{RELEASE_TAG}/LICENSE",
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        print(f"snapshotted {spec.api_symbol}: {fixture_path}")

    notebook_fixture_root = project_root / "datasets/fixtures/pymc" / LIBRARY_VERSION / "notebooks"
    notebook_manifest_root = (
        project_root / "datasets/raw/manifests/pymc" / LIBRARY_VERSION / "notebooks"
    )
    for source_path in NOTEBOOKS:
        source = _git(repository, "show", f"{RELEASE_TAG}:{source_path}")
        fixture_path = notebook_fixture_root / source_path
        manifest_path = notebook_manifest_root / f"{Path(source_path).stem}.json"
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_bytes(source)

        downloaded_at = _existing_downloaded_at(manifest_path) or acquisition_time
        last_modified = (
            _git(
                repository,
                "log",
                "-1",
                "--format=%cI",
                RELEASE_TAG,
                "--",
                source_path,
            )
            .decode()
            .strip()
        )
        source_name = Path(source_path).stem
        manifest = {
            "manifest_version": "1",
            "source_id": f"pymc-{LIBRARY_VERSION}-notebook-{source_name}",
            "library": "pymc",
            "library_version": LIBRARY_VERSION,
            "source_type": "notebook",
            "source_url": f"{UPSTREAM_URL}/blob/{RELEASE_TAG}/{source_path}",
            "release_tag": RELEASE_TAG,
            "release_url": f"{UPSTREAM_URL}/releases/tag/{RELEASE_TAG}",
            "source_commit": commit,
            "source_last_modified_at": last_modified,
            "downloaded_at": downloaded_at,
            "content_hash": sha256(source).hexdigest(),
            "media_type": "application/x-ipynb+json",
            "source_path": source_path,
            "license_name": "Apache-2.0",
            "license_url": f"{UPSTREAM_URL}/blob/{RELEASE_TAG}/LICENSE",
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        print(f"snapshotted notebook {source_name}: {fixture_path}")


def main() -> None:
    """Parse arguments and snapshot the fixed PyMC source selection."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        type=Path,
        required=True,
        help="Local clone containing the exact v6.1.0 tag.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="rag-pymc root receiving fixtures and manifests.",
    )
    arguments = parser.parse_args()
    snapshot(arguments.repository.resolve(), arguments.project_root.resolve())


if __name__ == "__main__":
    main()
