"""Core library for Docling normalization cluster."""

from .canonical import (
    jcs_canonical_bytes,
    sha256_hex,
    hash_canonical_without_integrity,
    compute_integrity,
    verify_integrity,
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
    "jcs_canonical_bytes",
    "sha256_hex",
    "hash_canonical_without_integrity",
    "compute_integrity",
    "verify_integrity",
    "l2_normalize",
    "z_score_normalize",
    "normalize_document_text",
    "NormalizationBackend",
    "LedgerWriter",
    "get_ledger",
]
