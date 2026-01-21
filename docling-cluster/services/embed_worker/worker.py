"""
Embed Worker - Creates embeddings using PyTorch (Batch Mode) and stores in Qdrant.
"""
import os
import sys
from typing import List, Dict, Any
import torch
from torch.utils.data import DataLoader, Dataset
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from redis import Redis
from rq import Queue, Worker

# Add parent paths for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, "/app")
from lib import (
    compute_chunk_id,
    get_ledger,
    hash_canonical_without_integrity
)
from schemas import ChunkEmbeddingV1, Chunker, Embedding, Provenance

# Configuration from environment
EMBEDDER_MODEL_ID = os.environ.get("EMBEDDER_MODEL_ID", "text-embedder-v1")
CHUNKER_VERSION = os.environ.get("CHUNKER_VERSION", "chunk.v1")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
QDRANT_HOST = os.environ.get("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
COLLECTION_NAME = "document_chunks"
EMBEDDING_DIM = 768
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "32"))

redis_conn = Redis.from_url(REDIS_URL)
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Ensure collection exists
try:
    qdrant_client.get_collection(COLLECTION_NAME)
except Exception:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )

# Mock weights hash
WEIGHTS_HASH = "sha256:" + "0" * 64

class ChunkDataset(Dataset):
    """Simple dataset for batch processing chunks."""
    def __init__(self, texts: List[str]):
        self.texts = texts

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        return self.texts[idx]

def l2_normalize(x: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    """L2 normalize a tensor along the last dimension."""
    return x / torch.clamp(torch.norm(x, p=2, dim=-1, keepdim=True), min=eps)

def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using PyTorch.
    Uses DataLoader for streamlined processing.
    """
    dataset = ChunkDataset(texts)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    all_embeddings = []
    
    # In production, this loop would move tensors to GPU and call the model
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # model.to(device)
    
    import hashlib
    for batch in dataloader:
        for text in batch:
            # Mock: Generate deterministic pseudo-embeddings for each text
            seed = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)
            torch.manual_seed(seed)
            v = torch.randn(EMBEDDING_DIM)
            v = l2_normalize(v)
            all_embeddings.append(v.tolist())
        
    return all_embeddings

def embed_batch(job_payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create embeddings for a list of document chunks and store in Qdrant as a batch.
    
    Args:
        job_payloads: List of dicts, each containing doc_id, chunk_index, chunk_text, etc.
    """
    if not job_payloads:
        return {"status": "empty_batch", "count": 0}

    print(f"[Scribe] Processing batch of {len(job_payloads)} chunks...")
    
    texts = [p["chunk_text"] for p in job_payloads]
    
    # 1. Vectorized Embedding Generation
    vectors = get_embeddings_batch(texts)
    
    points = []
    chunk_records = []
    ledger_records = []
    
    for i, payload in enumerate(job_payloads):
        doc_id = payload["doc_id"]
        chunk_index = payload["chunk_index"]
        chunk_text = payload["chunk_text"]
        source_block_refs = payload.get("source_block_refs", [])
        bundle_id = payload["bundle_id"]
        vector = vectors[i]
        
        # Compute chunk ID
        chunk_id = compute_chunk_id(doc_id, chunk_index, chunk_text)
        
        # Build chunk embedding record
        chunk_embedding = ChunkEmbeddingV1(
            doc_id=doc_id,
            chunk_id=chunk_id,
            chunk_text=chunk_text,
            chunker=Chunker(version=CHUNKER_VERSION),
            embedding=Embedding(
                framework="pytorch",
                model_id=EMBEDDER_MODEL_ID,
                weights_hash=WEIGHTS_HASH,
                dim=EMBEDDING_DIM,
                normalization="l2",
                vector=vector
            ),
            provenance=Provenance(source_block_refs=source_block_refs)
        )
        
        # Compute integrity hash
        chunk_dict = chunk_embedding.model_dump(by_alias=True, exclude_none=True)
        sha256_canonical = hash_canonical_without_integrity(chunk_dict)
        
        # Prepare Qdrant Point
        points.append(PointStruct(
            id=chunk_id.replace("sha256:", "")[:32],
            vector=vector,
            payload={
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "chunk_text": chunk_text[:500],
                "source_block_refs": source_block_refs
            }
        ))
        
        # Prepare Ledger Record
        ledger_records.append({
            "event": "chunk.embedding.v1",
            "bundle_id": bundle_id,
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "chunk_index": chunk_index,
            "embedder_model_id": EMBEDDER_MODEL_ID,
            "weights_hash": WEIGHTS_HASH,
            "content_hash": sha256_canonical
        })

    # 2. Batch Storage: Qdrant
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    
    # 3. Batch Logging: Ledger
    ledger = get_ledger()
    for record in ledger_records:
        ledger.append(record)
        
    print(f"[Scribe] Batch complete. {len(job_payloads)} chunks committed to Sovereign Vault.")
    
    return {
        "status": "batch_embedded",
        "count": len(job_payloads),
        "vector_dim": EMBEDDING_DIM
    }

if __name__ == "__main__":
    # Run as RQ worker
    worker = Worker(
        queues=[Queue("embed_queue", connection=redis_conn)],
        connection=redis_conn
    )
    worker.work()
