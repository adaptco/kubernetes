"""
Ingest API - FastAPI service for document ingestion.

Accepts documents via POST, generates bundle_id, and publishes to parse_queue.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from rq import Queue
import redis


app = FastAPI(
    title="Docling Ingest API",
    description="Document ingestion endpoint for the Docling normalization pipeline",
    version="0.1.0"
)

# Redis connection
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_conn = redis.from_url(REDIS_URL)
parse_queue = Queue("parse_queue", connection=redis_conn)


class IngestResponse(BaseModel):
    """Response from document ingestion."""
    bundle_id: str
    doc_id: str
    status: str
    queued_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    redis: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    try:
        redis_conn.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "error"
    
    return HealthResponse(status="ok", redis=redis_status)


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: Annotated[UploadFile, File(description="Document to ingest (PDF, DOCX, etc.)")],
    metadata: Annotated[str | None, Form()] = None
):
    """
    Ingest a document into the processing pipeline.
    """
    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Generate deterministic IDs
    content_hash = hashlib.sha256(content).hexdigest()
    doc_id = f"sha256:{content_hash}"
    bundle_id = f"bundle:{hashlib.sha256((doc_id + (file.filename or '')).encode()).hexdigest()[:16]}"
    
    # Prepare job payload
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "bundle_id": bundle_id,
        "doc_id": doc_id,
        "filename": file.filename,
        "content_type": file.filename or "application/octet-stream", # Using filename as fallback content type for mock
        "size_bytes": len(content),
        "metadata": metadata,
        "received_at": now,
    }
    
    # Publish to parse queue via RQ
    parse_queue.enqueue("worker.parse_document", job)
    
    return IngestResponse(
        bundle_id=bundle_id,
        doc_id=doc_id,
        status="queued",
        queued_at=now
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
