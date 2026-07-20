"""Source fetchers used by offline and controlled ingestion runs."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from rag_pymc.domain import SourceManifest
from rag_pymc.ingestion.errors import IngestionError, SourceIntegrityError


@dataclass(frozen=True, slots=True)
class LocalFileSourceFetcher:
    """Read and verify a previously acquired source artifact."""

    source_path: Path

    def fetch(self, manifest: SourceManifest) -> bytes:
        """Return bytes only when their SHA-256 matches the manifest."""
        try:
            source = self.source_path.read_bytes()
        except OSError as error:
            msg = f"unable to read source artifact: {self.source_path}"
            raise IngestionError(msg) from error

        actual_hash = sha256(source).hexdigest()
        if actual_hash != manifest.content_hash:
            msg = (
                f"source hash mismatch for {manifest.source_id}: "
                f"expected {manifest.content_hash}, got {actual_hash}"
            )
            raise SourceIntegrityError(msg)
        return source
