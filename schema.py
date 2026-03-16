"""
schema.py
---------
Pydantic model enforcing the canonical JSON schema for all scraped documents.
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
import re


SOURCE_TYPES = Literal["blog", "youtube", "pubmed"]


class ScrapedDocument(BaseModel):
    source_url: str = Field(..., description="Original URL or identifier of the content")
    source_type: SOURCE_TYPES = Field(..., description="One of: blog, youtube, pubmed")
    author: str = Field(default="Unknown", description="Author or channel name")
    published_date: str = Field(default="", description="ISO-8601 formatted date string")
    language: str = Field(default="en", description="ISO 639-1 two-letter language code")
    region: Optional[str] = Field(default=None, description="Geographic region if available")
    topic_tags: List[str] = Field(default_factory=list, description="NLP-extracted topic keywords")
    trust_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Heuristic trust score 0–1")
    content_chunks: List[str] = Field(default_factory=list, description="Chunked text segments")

    @field_validator("published_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Allow empty string or ISO-8601 compliant strings."""
        if not v:
            return v
        # Accept YYYY, YYYY-MM, YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS...
        pattern = r"^\d{4}(-\d{2}(-\d{2}(T[\d:+\-Z.]+)?)?)?$"
        if not re.match(pattern, v):
            raise ValueError(f"published_date must be ISO-8601 format, got: {v!r}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        if len(v) != 2 or not v.isalpha():
            return "en"  # graceful fallback
        return v.lower()

    @field_validator("topic_tags")
    @classmethod
    def clean_topic_tags(cls, v: List[str]) -> List[str]:
        return [t.strip() for t in v if t.strip()]

    @field_validator("content_chunks")
    @classmethod
    def clean_content_chunks(cls, v: List[str]) -> List[str]:
        return [c.strip() for c in v if c.strip()]

    model_config = {"json_schema_extra": {"examples": [
        {
            "source_url": "https://example.com/article",
            "source_type": "blog",
            "author": "Jane Doe",
            "published_date": "2024-01-15",
            "language": "en",
            "region": "US",
            "topic_tags": ["machine learning", "python"],
            "trust_score": 0.8,
            "content_chunks": ["First paragraph...", "Second paragraph..."]
        }
    ]}}
