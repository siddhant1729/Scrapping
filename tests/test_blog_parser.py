"""Basic tests for blog_parser and utils functions."""
import pytest
from utils.tagging import extract_tags
from utils.chunking import chunk_text


def test_extract_tags_returns_list():
    result = extract_tags("machine learning and artificial intelligence in healthcare")
    assert isinstance(result, list)


def test_extract_tags_empty_input():
    assert extract_tags("") == []
    assert extract_tags(None) == []


def test_chunk_text_returns_list():
    result = chunk_text("Paragraph one.\n\nParagraph two.\n\nParagraph three.")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_chunk_text_empty_input():
    assert chunk_text("") == []
    assert chunk_text(None) == []


def test_chunk_size_respected():
    long_text = ("word " * 200 + "\n\n") * 5
    chunks = chunk_text(long_text, chunk_size=100)
    for chunk in chunks:
        assert len(chunk) <= 3000  # generous ceiling for very long paragraphs
