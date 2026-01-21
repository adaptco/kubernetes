"""Core library for Docling normalization cluster."""

from .canonical import (
    hash_canonical_without_integrity,
    compute_integrity,
    verify_integrity,
    compute_chunk_id,
)
from .normalize import (
    l2_normalize,
    z_score_normalize,
    normalize_document_text,
    NormalizationBackend,
)
from .ledger import (
    LedgerWriter,
    get_ledger,
)

__all__ = [
    "hash_canonical_without_integrity",
    "compute_integrity",
    "verify_integrity",
    "compute_chunk_id",
    "l2_normalize",
    "z_score_normalize",
    "normalize_document_text",
    "NormalizationBackend",
    "LedgerWriter",
    "get_ledger",
]
