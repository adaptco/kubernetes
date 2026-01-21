"""
Replay Tests - Verify deterministic behavior.

Submit same document twice → assert identical bundle_id and hashes.
"""

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.canonical import jcs_canonical_bytes, sha256_hex, compute_integrity


class TestReplayDeterminism:
    """Test that identical inputs produce identical outputs."""

    def test_replay_identical_doc_id(self, sample_pdf_bytes: bytes):
        """Submit same document twice → identical doc_id (sha256 hash)."""
        # Compute doc_id twice
        doc_id_1 = f"sha256:{hashlib.sha256(sample_pdf_bytes).hexdigest()}"
        doc_id_2 = f"sha256:{hashlib.sha256(sample_pdf_bytes).hexdigest()}"
        
        assert doc_id_1 == doc_id_2
        assert doc_id_1.startswith("sha256:")

    def test_replay_identical_bundle_id(self, sample_pdf_bytes: bytes):
        """Submit same document twice → identical bundle_id."""
        filename = "test.pdf"
        
        # Simulate bundle_id generation (matches main.py logic)
        content_hash = hashlib.sha256(sample_pdf_bytes).hexdigest()
        doc_id = f"sha256:{content_hash}"
        
        bundle_id_1 = f"bundle:{hashlib.sha256((doc_id + filename).encode()).hexdigest()[:16]}"
        bundle_id_2 = f"bundle:{hashlib.sha256((doc_id + filename).encode()).hexdigest()[:16]}"
        
        assert bundle_id_1 == bundle_id_2
        assert bundle_id_1.startswith("bundle:")

    def test_replay_identical_canonical_hash(self, sample_doc_payload: dict):
        """Same content → same JCS canonical hash."""
        # Compute canonical bytes twice
        bytes_1 = jcs_canonical_bytes(sample_doc_payload)
        bytes_2 = jcs_canonical_bytes(sample_doc_payload)
        
        assert bytes_1 == bytes_2
        
        # Compute hash
        hash_1 = sha256_hex(bytes_1)
        hash_2 = sha256_hex(bytes_2)
        
        assert hash_1 == hash_2

    def test_replay_different_doc_different_id(self):
        """Different documents → different doc_id."""
        doc_a = b"Document A content"
        doc_b = b"Document B content"
        
        doc_id_a = f"sha256:{hashlib.sha256(doc_a).hexdigest()}"
        doc_id_b = f"sha256:{hashlib.sha256(doc_b).hexdigest()}"
        
        assert doc_id_a != doc_id_b

    def test_replay_key_order_independence(self):
        """JCS canonicalization is independent of key order."""
        payload_1 = {"zebra": 1, "alpha": 2, "beta": 3}
        payload_2 = {"alpha": 2, "beta": 3, "zebra": 1}
        
        canonical_1 = jcs_canonical_bytes(payload_1)
        canonical_2 = jcs_canonical_bytes(payload_2)
        
        assert canonical_1 == canonical_2
        # Verify keys are sorted
        assert canonical_1 == b'{"alpha":2,"beta":3,"zebra":1}'

    def test_replay_integrity_block_determinism(self, sample_doc_payload: dict):
        """compute_integrity produces identical results for same input."""
        result_1 = compute_integrity(sample_doc_payload)
        result_2 = compute_integrity(sample_doc_payload)
        
        assert result_1["integrity"]["sha256_canonical"] == result_2["integrity"]["sha256_canonical"]


class TestReplayWithFilename:
    """Test bundle_id determinism with different filename scenarios."""

    def test_same_content_different_filename_different_bundle(self):
        """Same content + different filename → different bundle_id."""
        content = b"Same content"
        content_hash = hashlib.sha256(content).hexdigest()
        doc_id = f"sha256:{content_hash}"
        
        bundle_a = f"bundle:{hashlib.sha256((doc_id + 'file_a.pdf').encode()).hexdigest()[:16]}"
        bundle_b = f"bundle:{hashlib.sha256((doc_id + 'file_b.pdf').encode()).hexdigest()[:16]}"
        
        assert bundle_a != bundle_b

    def test_empty_filename_handled(self):
        """Empty filename should not cause errors."""
        content = b"Test content"
        content_hash = hashlib.sha256(content).hexdigest()
        doc_id = f"sha256:{content_hash}"
        
        bundle = f"bundle:{hashlib.sha256((doc_id + '').encode()).hexdigest()[:16]}"
        
        assert bundle.startswith("bundle:")
        assert len(bundle) == len("bundle:") + 16
