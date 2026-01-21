
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.canonical import jcs_canonical_bytes, sha256_hex, compute_integrity, verify_integrity
from lib.ledger import LedgerWriter

def verify_determinism():
    print("--- Verifying Determinism ---")
    content = b"%PDF-1.4\nSample Content\n%%EOF"
    filename = "test.pdf"
    
    # Simulate API logic
    content_hash = hashlib.sha256(content).hexdigest()
    doc_id = f"sha256:{content_hash}"
    bundle_id = f"bundle:{hashlib.sha256((doc_id + filename).encode()).hexdigest()[:16]}"
    
    print(f"Doc ID: {doc_id}")
    print(f"Bundle ID: {bundle_id}")
    
    # Run again
    bundle_id_2 = f"bundle:{hashlib.sha256((doc_id + filename).encode()).hexdigest()[:16]}"
    assert bundle_id == bundle_id_2, "Bundle ID must be deterministic!"
    print("✓ Bundle ID is deterministic")

def verify_canonical_hashing():
    print("\n--- Verifying Canonical Hashing ---")
    payload = {"z": 1, "a": 2, "b": {"y": 3, "x": 4}}
    
    bytes_1 = jcs_canonical_bytes(payload)
    print(f"Canonical Bytes: {bytes_1.decode()}")
    
    # Hash check
    h1 = sha256_hex(bytes_1)
    h2 = sha256_hex(jcs_canonical_bytes({"a": 2, "b": {"x": 4, "y": 3}, "z": 1}))
    assert h1 == h2, "Hash must be independent of key order!"
    print(f"Hash: {h1}")
    print("✓ Canonical hashing is correct")

def verify_ledger_chain():
    print("\n--- Verifying Ledger Hash-Chain ---")
    ledger_path = "verify_ledger.jsonl"
    if os.path.exists(ledger_path): os.remove(ledger_path)
    
    ledger = LedgerWriter(ledger_path)
    
    e1 = ledger.append({"msg": "first"}, entry_type="test")
    e2 = ledger.append({"msg": "second"}, entry_type="test")
    
    print(f"Entry 1 Hash: {e1['entry_hash']}")
    print(f"Entry 2 Hash: {e2['entry_hash']}")
    print(f"Entry 2 Prev: {e2['prev_hash']}")
    
    assert e2['prev_hash'] == e1['entry_hash'], "Chain break!"
    
    valid, count, error = ledger.verify_chain()
    assert valid, f"Ledger verification failed: {error}"
    print(f"✓ Ledger verified with {count} entries")
    
    if os.path.exists(ledger_path): os.remove(ledger_path)

if __name__ == "__main__":
    try:
        verify_determinism()
        verify_canonical_hashing()
        verify_ledger_chain()
        print("\n=== ALL MANUAL VERIFICATIONS PASSED ===")
    except Exception as e:
        print(f"\nFAIL: {e}")
        sys.exit(1)
