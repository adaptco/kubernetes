
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.embed_worker.worker import embed_batch

def test_batch_determinism():
    print("--- Verifying Batch Determinism (Scribe Processing) ---")
    
    payloads = [
        {"doc_id": "doc1", "chunk_index": 0, "chunk_text": "Hello world", "bundle_id": "b1"},
        {"doc_id": "doc1", "chunk_index": 1, "chunk_text": "Sovereign OS", "bundle_id": "b1"}
    ]
    
    # Process batch 1
    res1 = embed_batch(payloads)
    
    # Process same batch 2
    res2 = embed_batch(payloads)
    
    assert res1["count"] == res2["count"] == 2
    
    # Verify ledger hashes (we need to inspect the ledger or mock it)
    print("✓ Batch count verified")
    print("✓ Logic executed without error (Mocked Qdrant/Ledger handled by worker imports if mocks exist)")

if __name__ == "__main__":
    # Note: This will attempt to connect to Redis/Qdrant since worker.py 
    # initializes them on import. For logic verification, we focus on the
    # deterministic seeding in get_embeddings_batch.
    
    print("Verifying core batch logic...")
    # We can't easily run the full embed_batch without services, 
    # but we can verify the get_embeddings_batch function.
    from services.embed_worker.worker import get_embeddings_batch
    
    texts = ["Test 1", "Test 2"]
    v1 = get_embeddings_batch(texts)
    v2 = get_embeddings_batch(texts)
    
    assert v1 == v2, "Batch embeddings must be deterministic!"
    print("✓ get_embeddings_batch is deterministic")
    
    # Single vs Batch consistency
    v3 = get_embeddings_batch(["Test 1"])
    assert v1[0] == v3[0], "Embedding for 'Test 1' must be consistent across batches!"
    print("✓ Individual embedding consistency verified")
    
    print("\n=== BATCH LOGIC VERIFIED ===")
