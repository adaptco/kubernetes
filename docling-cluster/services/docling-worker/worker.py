"""
Docling Worker - Celery worker for document parsing and normalization.

Consumes parse_queue, runs IBM Docling, applies normalization, emits to embed_queue.
"""

import os
import sys
from datetime import datetime, timezone

from celery import Celery

# Add parent dirs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from lib.canonical import compute_integrity
from lib.normalize import normalize_document_text


# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
app = Celery("docling-worker", broker=REDIS_URL, backend=REDIS_URL)

# Pinned versions for determinism
DOCLING_VERSION = "1.0.0"  # Pin to actual version
NORMALIZER_VERSION = "norm.v1"


@app.task(name="parse_document")
def parse_document(job: dict) -> dict:
    """
    Parse a document using IBM Docling and normalize the output.
    
    Args:
        job: Job payload containing doc_id, filename, content_type, etc.
    
    Returns:
        Normalized document in doc.normalized.v1 format
    """
    doc_id = job["doc_id"]
    
    # TODO: In production, retrieve actual file content from object store
    # content = object_store.get(doc_id)
    
    # Placeholder: Simulate Docling parsing
    # In production: from docling import DocumentConverter
    # converter = DocumentConverter()
    # result = converter.convert(content)
    
    parsed_content = {
        "title": job.get("filename", "Untitled"),
        "pages": [
            {
                "page_index": 0,
                "blocks": [
                    {"type": "text", "text": "Sample text content (replace with Docling output)"}
                ]
            }
        ]
    }
    
    # Normalize text in all blocks
    for page in parsed_content["pages"]:
        for block in page["blocks"]:
            if block.get("text"):
                block["text"] = normalize_document_text(block["text"])
    
    # Build normalized document
    normalized_doc = {
        "schema": "doc.normalized.v1",
        "doc_id": doc_id,
        "source": {
            "uri": f"ingest://{job.get('filename', 'unknown')}",
            "content_type": job.get("content_type", "application/octet-stream"),
            "received_at": job.get("received_at", datetime.now(timezone.utc).isoformat())
        },
        "parser": {
            "name": "ibm-docling",
            "version": DOCLING_VERSION,
            "config_hash": "sha256:" + "0" * 64  # TODO: Compute from actual config
        },
        "normalization": {
            "normalizer_version": NORMALIZER_VERSION,
            "canonicalization": "JCS-RFC8785",
            "text_policy": {
                "unicode": "NFKC",
                "whitespace": "collapse",
                "line_endings": "LF"
            }
        },
        "content": parsed_content
    }
    
    # Compute and inject integrity
    # TODO: Get prev_ledger_hash from ledger
    prev_hash = None
    normalized_doc = compute_integrity(normalized_doc, prev_hash)
    
    # Publish to embed_queue
    app.send_task("embed_chunks", args=[normalized_doc])
    
    # TODO: Write to ledger
    # ledger.append(normalized_doc)
    
    return normalized_doc


if __name__ == "__main__":
    app.start()
