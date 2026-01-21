"""
Pydantic schema for chunk.embedding.v1

Represents a document chunk with its embedding vector and provenance.
"""

from typing import Literal
from pydantic import BaseModel, Field


class ChunkerParams(BaseModel):
    """Parameters used for chunking."""
    max_tokens: int = 400
    overlap: int = 60


class Chunker(BaseModel):
    """Information about the chunker used."""
    version: str = "chunk.v1"
    method: Literal["block+window", "sentence", "paragraph", "fixed"] = "block+window"
    params: ChunkerParams = Field(default_factory=ChunkerParams)


class Embedding(BaseModel):
    """Information about the embedding model and normalization."""
    framework: Literal["pytorch", "jax"] = "pytorch"
    model_id: str
    weights_hash: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    dim: int
    normalization: Literal["l2", "none"] = "l2"
    vector: list[float]


class Provenance(BaseModel):
    """Provenance tracking back to source blocks."""
    source_block_refs: list[str]  # Format: "p{page}:b{block}"


class IntegrityBlock(BaseModel):
    """Hash-chain integrity information."""
    sha256_canonical: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    prev_ledger_hash: str | None = Field(None, pattern=r"^sha256:[a-f0-9]{64}$")


class ChunkEmbeddingV1(BaseModel):
    """
    Schema: chunk.embedding.v1
    
    Represents a document chunk with its embedding vector,
    chunker provenance, and hash-chain integrity.
    """
    schema_: Literal["chunk.embedding.v1"] = Field("chunk.embedding.v1", alias="schema")
    doc_id: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    chunk_id: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    chunk_text: str  # Added as requested
    chunker: Chunker = Field(default_factory=Chunker)
    embedding: Embedding
    provenance: Provenance
    integrity: IntegrityBlock | None = None  # Make optional for initial creation

    model_config = {"populate_by_name": True}
