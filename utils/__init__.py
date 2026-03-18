"""
utils/__init__.py
------------------
Public API of the utils package.
Exports the two most commonly used utilities for convenience.
"""

from utils.tagging import extract_tags
from utils.chunking import chunk_text

__all__ = ["extract_tags", "chunk_text"]
