"""
Pytest fixtures for docling-cluster verification tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Import library modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.ledger import LedgerWriter
from lib.canonical import jcs_canonical_bytes, sha256_hex


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Simulated PDF content for testing."""
    return b"%PDF-1.4\nSample PDF content for testing determinism\n%%EOF"


@pytest.fixture
def sample_text_content() -> str:
    """Sample text content for normalization tests."""
    return "Hello World\n\nThis is a test document."


@pytest.fixture
def sample_doc_payload() -> dict:
    """Sample normalized document payload."""
    return {
        "schema": "doc.normalized.v1",
        "doc_id": "sha256:abc123",
        "content": {
            "title": "Test Document",
            "pages": [{"page_index": 0, "blocks": []}]
        }
    }


# ============================================================================
# Ledger Fixtures
# ============================================================================

@pytest.fixture
def temp_ledger_path(tmp_path: Path) -> Path:
    """Provide a temporary ledger file path."""
    return tmp_path / "test_ledger.jsonl"


@pytest.fixture
def ledger(temp_ledger_path: Path) -> LedgerWriter:
    """Create a fresh ledger writer for testing."""
    return LedgerWriter(temp_ledger_path)


# ============================================================================
# Mock Redis Fixtures
# ============================================================================

@pytest.fixture
def mock_redis() -> Generator[MagicMock, None, None]:
    """Mock Redis client for queue testing."""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.lpush.return_value = 1
    mock.lrange.return_value = []
    
    with patch("redis.from_url", return_value=mock):
        yield mock


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def api_client(mock_redis: MagicMock) -> TestClient:
    """Create FastAPI test client with mocked Redis."""
    from services.ingest_api.main import app
    
    # Inject mock redis
    with patch.dict("services.ingest_api.main.__dict__", {"redis_client": mock_redis}):
        return TestClient(app)
