"""
Embed Worker - Celery worker for chunking and embedding generation.

Consumes embed_queue, chunks documents, generates embeddings, stores in Qdrant.
"""

import os
import sys
from typing import Any

from celery import Celery
import torch
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# Add parent dirs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from lib.canonical import compute_integrity, sha256_hex, jcs_canonical_bytes
from lib.normalize import l2_normalize


# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

app = Celery("embed-worker", broker=REDIS_URL, backend=REDIS_URL)

# Pinned versions for determinism
CHUNKER_VERSION = "chunk.v1"
EMBEDDER_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Qdrant client
qdrant: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    """Get or create Qdrant client."""
    global qdrant
    if qdrant is None:
        qdrant = QdrantClient(url=QDRANT_URL)
        # Ensure collection exists
        try:
            qdrant.get_collection("chunks")
        except Exception:
            qdrant.create_collection(
                collection_name="chunks",
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
            )
    return qdrant


def chunk_document(content: dict, max_tokens: int = 400, overlap: int = 60) -> list[dict]:
    """
    Deterministically chunk document content.
    
    Returns list of chunks with block references.
    """
    chunks = []
    
    for page in content.get("pages", []):
        page_idx = page["page_index"]
        current_text = ""
        current_refs = []
        
        for block_idx, block in enumerate(page.get("blocks", [])):
            if block.get("type") == "text" and block.get("text"):
                text = block["text"]
                ref = f"p{page_idx}:b{block_idx}"
                
                # Simple chunking by block (in production: use tokenizer)
                if len(current_text) + len(text) > max_tokens * 4:  # Approx char count
                    if current_text:
                        chunks.append({
                            "text": current_text.strip(),
                            "refs": current_refs
                        })
                    current_text = text[-overlap * 4:] if overlap else ""
                    current_refs = [ref]
                else:
                    current_text += " " + text
                    current_refs.append(ref)
        
        if current_text.strip():
            chunks.append({
                "text": current_text.strip(),
                "refs": current_refs
            })
    
    return chunks


def generate_embedding(text: str) -> torch.Tensor:
    """
    Generate embedding for text using the pinned model.
    
    In production: load actual model and tokenizer.
    """
    # Placeholder: Random embedding (replace with actual model inference)
    # from transformers import AutoTokenizer, AutoModel
    # tokenizer = AutoTokenizer.from_pretrained(EMBEDDER_MODEL_ID)
    # model = AutoModel.from_pretrained(EMBEDDER_MODEL_ID)
    # inputs = tokenizer(text, return_tensors="pt", truncation=True)
    # outputs = model(**inputs)
    # embedding = outputs.last_hidden_state.mean(dim=1)
    
    torch.manual_seed(hash(text) % (2**32))  # Deterministic for demo
    embedding = torch.randn(EMBEDDING_DIM)
    
    return l2_normalize(embedding)


@app.task(name="embed_chunks")
def embed_chunks(normalized_doc: dict) -> list[dict]:
    """
    Chunk and embed a normalized document.
    
    Args:
        normalized_doc: Document in doc.normalized.v1 format
    
    Returns:
        List of chunk embeddings in chunk.embedding.v1 format
    """
    doc_id = normalized_doc["doc_id"]
    content = normalized_doc["content"]
    prev_hash = normalized_doc["integrity"]["sha256_canonical"]
    
    chunks = chunk_document(content)
    results = []
    
    client = get_qdrant()
    points = []
    
    for chunk in chunks:
        # Generate chunk ID from content
        chunk_content_hash = sha256_hex(jcs_canonical_bytes(chunk))
        chunk_id = f"sha256:{chunk_content_hash}"
        
        # Generate embedding
        embedding = generate_embedding(chunk["text"])
        vector = embedding.tolist()
        
        # Build chunk embedding record
        chunk_embedding = {
            "schema": "chunk.embedding.v1",
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "chunker": {
                "version": CHUNKER_VERSION,
                "method": "block+window",
                "params": {"max_tokens": 400, "overlap": 60}
            },
            "embedding": {
                "framework": "pytorch",
                "model_id": EMBEDDER_MODEL_ID,
                "weights_hash": "sha256:" + "0" * 64,  # TODO: Compute from actual weights
                "dim": EMBEDDING_DIM,
                "normalization": "l2",
                "vector": vector
            },
            "provenance": {
                "source_block_refs": chunk["refs"]
            }
        }
        
        # Compute integrity
        chunk_embedding = compute_integrity(chunk_embedding, prev_hash)
        prev_hash = chunk_embedding["integrity"]["sha256_canonical"]
        
        results.append(chunk_embedding)
        
        # Prepare for Qdrant
        points.append(PointStruct(
            id=chunk_content_hash[:32],  # Use first 32 chars as ID
            vector=vector,
            payload={
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "text": chunk["text"]
            }
        ))
    
    # Upsert to Qdrant
    if points:
        client.upsert(collection_name="chunks", points=points)
    
    # TODO: Write to ledger
    # for record in results:
    #     ledger.append(record)
    
    return results


if __name__ == "__main__":
    app.start()
