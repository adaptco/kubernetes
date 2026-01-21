"""
Ledger Writer - Append-only hash-chain ledger for deterministic replay.

Provides fail-closed integrity verification and audit trail.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.canonical import jcs_canonical_bytes, sha256_hex


class LedgerWriter:
    """
    Append-only JSONL ledger with hash-chain integrity.
    
    Each entry contains:
    - The canonical payload
    - SHA256 hash of the entry
    - Link to previous entry hash (hash-chain)
    """
    
    def __init__(self, ledger_path: str | Path = "ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
        self._last_hash: str | None = None
        
        # Load last hash from existing ledger
        if self.ledger_path.exists():
            self._last_hash = self._read_last_hash()
    
    def _read_last_hash(self) -> str | None:
        """Read the hash of the last entry in the ledger."""
        if not self.ledger_path.exists():
            return None
        
        last_line = None
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line
        
        if last_line:
            try:
                entry = json.loads(last_line)
                return entry.get("entry_hash")
            except json.JSONDecodeError:
                return None
        return None
    
    def append(self, payload: dict[str, Any], entry_type: str = "record") -> dict[str, Any]:
        """
        Append an entry to the ledger.
        
        Args:
            payload: The data to record
            entry_type: Type of entry (e.g., "doc.normalized.v1", "chunk.embedding.v1")
        
        Returns:
            The ledger entry with hash-chain metadata
        """
        # Build ledger entry
        entry = {
            "entry_type": entry_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_hash": self._last_hash,
            "payload": payload
        }
        
        # Compute entry hash
        entry_hash = sha256_hex(jcs_canonical_bytes(entry))
        entry["entry_hash"] = entry_hash
        
        # Append to ledger file
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
        
        # Update chain
        self._last_hash = entry_hash
        
        return entry
    
    def verify_chain(self) -> tuple[bool, int, str | None]:
        """
        Verify the integrity of the entire ledger.
        
        Returns:
            (valid, entry_count, error_message)
        """
        if not self.ledger_path.exists():
            return True, 0, None
        
        prev_hash = None
        count = 0
        
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as e:
                    return False, count, f"Line {line_num}: Invalid JSON - {e}"
                
                # Verify prev_hash link
                if entry.get("prev_hash") != prev_hash:
                    return False, count, f"Line {line_num}: Chain break - expected prev_hash {prev_hash}"
                
                # Verify entry hash
                claimed_hash = entry.pop("entry_hash", None)
                computed_hash = sha256_hex(jcs_canonical_bytes(entry))
                entry["entry_hash"] = claimed_hash  # Restore
                
                if claimed_hash != computed_hash:
                    return False, count, f"Line {line_num}: Hash mismatch - claimed {claimed_hash}, computed {computed_hash}"
                
                prev_hash = claimed_hash
                count += 1
        
        return True, count, None
    
    def get_last_hash(self) -> str | None:
        """Get the hash of the most recent entry."""
        return self._last_hash


# Singleton instance for workers
_ledger: LedgerWriter | None = None


def get_ledger(path: str | None = None) -> LedgerWriter:
    """Get or create the singleton ledger instance."""
    global _ledger
    if _ledger is None:
        ledger_path = path or os.getenv("LEDGER_PATH", "ledger.jsonl")
        _ledger = LedgerWriter(ledger_path)
    return _ledger
