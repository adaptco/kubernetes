"""
Pydantic schema for doc.normalized.v1

Represents a Docling-parsed document after canonicalization and normalization.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class TextPolicy(BaseModel):
    """Text normalization policy applied to document content."""
    unicode: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFKC"
    whitespace: Literal["collapse", "preserve"] = "collapse"
    line_endings: Literal["LF", "CRLF"] = "LF"


class ParserInfo(BaseModel):
    """Information about the parser used."""
    name: str = "ibm-docling"
    version: str
    config_hash: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")


class NormalizationInfo(BaseModel):
    """Normalization configuration applied."""
    normalizer_version: str = "norm.v1"
    canonicalization: Literal["JCS-RFC8785"] = "JCS-RFC8785"
    text_policy: TextPolicy = Field(default_factory=TextPolicy)


class DocumentSource(BaseModel):
    """Source information for the original document."""
    uri: str
    content_type: str
    received_at: datetime


class ContentBlock(BaseModel):
    """A content block within a page."""
    type: Literal["text", "table", "image", "heading", "list", "code"]
    text: str | None = None
    cells: list[list[str]] | None = None  # For tables


class Page(BaseModel):
    """A page in the document."""
    page_index: int
    blocks: list[ContentBlock]


class DocumentContent(BaseModel):
    """Structured content of the document."""
    title: str | None = None
    pages: list[Page]


class IntegrityBlock(BaseModel):
    """Hash-chain integrity information."""
    sha256_canonical: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    prev_ledger_hash: str | None = Field(None, pattern=r"^sha256:[a-f0-9]{64}$")


class DocNormalizedV1(BaseModel):
    """
    Schema: doc.normalized.v1
    
    Represents a document parsed by IBM Docling with deterministic
    normalization applied for hash-chain integrity.
    """
    schema_: Literal["doc.normalized.v1"] = Field("doc.normalized.v1", alias="schema")
    doc_id: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    source: DocumentSource
    parser: ParserInfo
    normalization: NormalizationInfo = Field(default_factory=NormalizationInfo)
    content: DocumentContent
    integrity: IntegrityBlock

    model_config = {"populate_by_name": True}
