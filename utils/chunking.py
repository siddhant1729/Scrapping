"""
utils/chunking.py
------------------
Content chunking module.
Splits long text into smaller segments for downstream processing.
Called by all parsers to generate content_chunks for the JSON output.
"""

import re
from typing import List


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """
    Split text into chunks of approximately chunk_size characters.
    Splits on paragraph boundaries first (double newline).
    Returns a list of non-empty string chunks.
    Returns [] if text is None or empty.
    """
    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    if not paragraphs:
        return [text.strip()]

    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current += (" " if current else "") + para
        else:
            if current:
                chunks.append(current.strip())
            current = para

    if current:
        chunks.append(current.strip())

    return chunks if chunks else [text.strip()]


def chunk_transcript(segments: list, max_words: int = 200) -> List[str]:
    """
    Chunk YouTube transcript segments (list of dicts with 'text' key)
    into logical groups by word count.
    """
    chunks: List[str] = []
    current: List[str] = []
    current_words = 0

    for seg in segments:
        text = seg.get("text", "").strip() if isinstance(seg, dict) else str(seg).strip()
        if not text:
            continue
        words = len(text.split())
        if current_words + words > max_words and current:
            chunks.append(" ".join(current))
            current = []
            current_words = 0
        current.append(text)
        current_words += words

    if current:
        chunks.append(" ".join(current))

    return chunks
