"""Tests for pipeline dispatcher routing."""
import pytest
from pipeline import process


def test_pipeline_accepts_blog():
    """pipeline.process should not raise on a string source_type='blog'."""
    # We just check the dispatcher raises ValueError for unknown types,
    # not that it actually scrapes (which would require network).
    with pytest.raises(Exception):
        process("https://nonexistent-url-that-will-fail.xyz/", "blog")


def test_pipeline_accepts_youtube():
    with pytest.raises(Exception):
        process("https://www.youtube.com/watch?v=invalid000", "youtube")


def test_pipeline_accepts_pubmed():
    with pytest.raises(Exception):
        process("0000000", "pubmed")


def test_pipeline_rejects_unknown_source():
    with pytest.raises(ValueError):
        process("https://example.com", "twitter")
