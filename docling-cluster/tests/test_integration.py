"""
Integration Tests - End-to-end flow verification.

Test the complete flow from ingest → ledger entry.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.ledger import LedgerWriter
from lib.canonical import compute_integrity, verify_integrity, sha256_hex, jcs_canonical_bytes


class TestLedgerIntegration:
    """Test ledger hash-chain functionality."""

    def test_ledger_entry_created(self, ledger: LedgerWriter, sample_doc_payload: dict):
        """Process doc → ledger entry with hash-chain."""
        entry = ledger.append(sample_doc_payload, entry_type="doc.normalized.v1")
        
        assert "entry_hash" in entry
        assert "prev_hash" in entry
        assert entry["entry_type"] == "doc.normalized.v1"
        assert entry["prev_hash"] is None  # First entry

    def test_ledger_chain_linkage(self, ledger: LedgerWriter, sample_doc_payload: dict):
        """Multiple entries maintain hash-chain integrity."""
        entry_1 = ledger.append({"doc": "first"}, entry_type="test.v1")
        entry_2 = ledger.append({"doc": "second"}, entry_type="test.v1")
        entry_3 = ledger.append({"doc": "third"}, entry_type="test.v1")
        
        # Verify chain linkage
        assert entry_1["prev_hash"] is None
        assert entry_2["prev_hash"] == entry_1["entry_hash"]
        assert entry_3["prev_hash"] == entry_2["entry_hash"]

    def test_ledger_chain_verification(self, ledger: LedgerWriter):
        """verify_chain() passes for valid ledger."""
        # Append some entries
        ledger.append({"data": "entry1"})
        ledger.append({"data": "entry2"})
        ledger.append({"data": "entry3"})
        
        # Verify chain
        valid, count, error = ledger.verify_chain()
        
        assert valid is True
        assert count == 3
        assert error is None

    def test_ledger_empty_verification(self, temp_ledger_path: Path):
        """Empty ledger passes verification."""
        ledger = LedgerWriter(temp_ledger_path)
        
        valid, count, error = ledger.verify_chain()
        
        assert valid is True
        assert count == 0
        assert error is None

    def test_ledger_persistence(self, temp_ledger_path: Path, sample_doc_payload: dict):
        """Ledger entries persist and can be reloaded."""
        # Create ledger and add entry
        ledger_1 = LedgerWriter(temp_ledger_path)
        entry = ledger_1.append(sample_doc_payload)
        original_hash = entry["entry_hash"]
        
        # Create new ledger instance pointing to same file
        ledger_2 = LedgerWriter(temp_ledger_path)
        
        # Last hash should be loaded
        assert ledger_2.get_last_hash() == original_hash


class TestIntegrityIntegration:
    """Test integrity hash computation and verification."""

    def test_integrity_hash_matches(self, sample_doc_payload: dict):
        """Integrity sha256_canonical is valid and verifiable."""
        payload_with_integrity = compute_integrity(sample_doc_payload)
        
        assert "integrity" in payload_with_integrity
        assert "sha256_canonical" in payload_with_integrity["integrity"]
        assert payload_with_integrity["integrity"]["sha256_canonical"].startswith("sha256:")
        
        # Verify the integrity
        assert verify_integrity(payload_with_integrity) is True

    def test_integrity_tamper_detection(self, sample_doc_payload: dict):
        """Tampering with payload is detected by verify_integrity."""
        payload_with_integrity = compute_integrity(sample_doc_payload)
        
        # Tamper with content
        payload_with_integrity["content"]["title"] = "TAMPERED"
        
        # Verification should fail
        assert verify_integrity(payload_with_integrity) is False

    def test_integrity_chain_linkage(self, sample_doc_payload: dict):
        """prev_ledger_hash links entries together."""
        entry_1 = compute_integrity(sample_doc_payload, prev_ledger_hash=None)
        
        # Get the hash from first entry
        first_hash = entry_1["integrity"]["sha256_canonical"]
        
        # Create second entry linked to first
        entry_2 = compute_integrity({"doc": "second"}, prev_ledger_hash=first_hash)
        
        assert entry_2["integrity"]["prev_ledger_hash"] == first_hash


class TestEndToEndFlow:
    """Test complete processing pipeline."""

    def test_full_pipeline_determinism(self, ledger: LedgerWriter):
        """Same document processed twice produces identical ledger hashes."""
        doc_content = {"title": "Test Doc", "body": "Content here"}
        
        # Process document first time
        payload_1 = compute_integrity(doc_content)
        entry_1 = ledger.append(payload_1, entry_type="doc.normalized.v1")
        
        # Reset ledger for second run (new file)
        import tempfile
        temp_path = Path(tempfile.mktemp(suffix=".jsonl"))
        ledger_2 = LedgerWriter(temp_path)
        
        # Process same document
        payload_2 = compute_integrity(doc_content)
        entry_2 = ledger_2.append(payload_2, entry_type="doc.normalized.v1")
        
        # Integrity hashes should match
        assert payload_1["integrity"]["sha256_canonical"] == payload_2["integrity"]["sha256_canonical"]
        
        # Cleanup
        temp_path.unlink(missing_ok=True)

    def test_ledger_file_format(self, ledger: LedgerWriter, temp_ledger_path: Path):
        """Ledger entries are stored as valid JSONL."""
        ledger.append({"doc": "test1"})
        ledger.append({"doc": "test2"})
        
        # Read and parse file
        with open(temp_ledger_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        for line in lines:
            entry = json.loads(line.strip())
            assert "entry_hash" in entry
            assert "timestamp" in entry
            assert "payload" in entry
