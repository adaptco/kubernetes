"""
Normalization utilities for document content and embeddings.
Provides deterministic normalization with PyTorch (JAX-swappable abstraction).
"""

import unicodedata
import re
from typing import Literal

import torch


# ============================================================================
# Embedding Normalization (Vector Space)
# ============================================================================

def l2_normalize(x: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    """
    L2-normalize vectors along the last dimension.
    
    Args:
        x: Input tensor of shape (..., dim)
        eps: Small constant for numerical stability
    
    Returns:
        Unit-length vectors (L2 norm = 1)
    """
    norm = torch.norm(x, p=2, dim=-1, keepdim=True)
    return x / torch.clamp(norm, min=eps)


def z_score_normalize(
    x: torch.Tensor,
    mean: torch.Tensor,
    std: torch.Tensor,
    eps: float = 1e-12
) -> torch.Tensor:
    """
    Z-score normalization using pre-computed statistics.
    
    NOTE: Statistics must be computed as a SEPARATE, LEDGERED JOB.
    Never compute implicit statistics during inference.
    
    Args:
        x: Input tensor
        mean: Pre-computed mean (must be ledgered)
        std: Pre-computed standard deviation (must be ledgered)
        eps: Small constant for numerical stability
    """
    return (x - mean) / torch.clamp(std, min=eps)


# ============================================================================
# Document Content Normalization (Text Processing)
# ============================================================================

def normalize_unicode(text: str, form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFKC") -> str:
    """
    Apply Unicode normalization.
    
    Default: NFKC (Compatibility Composition) for maximum compatibility.
    """
    return unicodedata.normalize(form, text)


def collapse_whitespace(text: str) -> str:
    """
    Collapse runs of whitespace to single spaces, preserving paragraph boundaries.
    
    - Multiple spaces → single space
    - Multiple newlines → double newline (paragraph break)
    - Tabs → space
    """
    # Normalize line endings to LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Preserve paragraph breaks (2+ newlines → exactly 2)
    text = re.sub(r"\n{2,}", "\n\n", text)
    
    # Collapse other whitespace runs
    text = re.sub(r"[ \t]+", " ", text)
    
    # Clean up spaces around paragraph breaks
    text = re.sub(r" *\n *", "\n", text)
    
    return text.strip()


def normalize_line_endings(text: str) -> str:
    """Convert all line endings to LF (Unix-style)."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_document_text(text: str) -> str:
    """
    Full document text normalization pipeline.
    
    1. Unicode NFKC normalization
    2. Line endings → LF
    3. Whitespace collapse (preserving paragraphs)
    """
    text = normalize_unicode(text, "NFKC")
    text = normalize_line_endings(text)
    text = collapse_whitespace(text)
    return text


# ============================================================================
# JAX Abstraction Layer (for future swap)
# ============================================================================

class NormalizationBackend:
    """
    Thin abstraction layer for normalization operations.
    Enables swapping PyTorch → JAX without changing calling code.
    """
    
    def __init__(self, backend: Literal["pytorch", "jax"] = "pytorch"):
        self.backend = backend
        if backend == "jax":
            raise NotImplementedError("JAX backend not yet implemented. Set backend='pytorch'.")
    
    def l2_normalize(self, x: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
        """L2 normalize using configured backend."""
        if self.backend == "pytorch":
            return l2_normalize(x, eps)
        raise NotImplementedError(f"Backend {self.backend} not implemented")
