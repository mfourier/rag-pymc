"""Shared deterministic serialization primitives for content identities."""

import json
from hashlib import sha256


def canonical_json_bytes(value: object) -> bytes:
    """Serialize a JSON-compatible value with the project's canonical policy."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def canonical_json_sha256(value: object) -> str:
    """Hash a JSON-compatible value after canonical serialization."""
    return sha256(canonical_json_bytes(value)).hexdigest()
