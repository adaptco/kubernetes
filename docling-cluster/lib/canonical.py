"""
Canonicalization utilities for deterministic JSON serialization and hashing.
Implements JCS-compatible (RFC8785) canonical JSON for hash-chain integrity.
"""

import hashlib
import json
from typing import Any


def jcs_canonical_bytes(obj: dict[str, Any]) -> bytes:
    """
    Serialize a dictionary to JCS-canonical JSON bytes.
    
    - Keys sorted lexicographically
    - No whitespace
    - Deterministic output
    
    For strict RFC8785 compliance, consider using a dedicated JCS library.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Compute SHA256 hash and return as hex string."""
    return hashlib.sha256(data).hexdigest()


def hash_canonical_without_integrity(payload: dict[str, Any]) -> str:
    """
    Compute canonical hash of a payload, excluding the 'integrity' field.
    
    This enables fail-closed re-derivable hashes:
    1. Remove 'integrity' field
    2. Canonicalize remaining payload
    3. Compute SHA256
    4. Inject hash back into 'integrity.sha256_canonical'
    """
    tmp = dict(payload)
    tmp.pop("integrity", None)
    return sha256_hex(jcs_canonical_bytes(tmp))


def compute_integrity(payload: dict[str, Any], prev_ledger_hash: str | None = None) -> dict[str, Any]:
    """
    Compute and inject integrity block into payload.
    
    Returns a new dict with the 'integrity' field populated.
    """
    result = dict(payload)
    result.pop("integrity", None)
    
    canonical_hash = sha256_hex(jcs_canonical_bytes(result))
    
    result["integrity"] = {
        "sha256_canonical": f"sha256:{canonical_hash}",
        "prev_ledger_hash": prev_ledger_hash
    }
    
    return result


def verify_integrity(payload: dict[str, Any]) -> bool:
    """
    Verify that a payload's integrity hash matches its content.
    
    Returns True if valid, False otherwise.
    """
    if "integrity" not in payload:
        return False
    
    claimed_hash = payload["integrity"].get("sha256_canonical", "")
    if claimed_hash.startswith("sha256:"):
        claimed_hash = claimed_hash[7:]
    
    computed_hash = hash_canonical_without_integrity(payload)
    
    return claimed_hash == computed_hash
