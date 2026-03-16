"""
utils.py
--------
Shared utilities: language detection, topic tagging, text chunking, trust scoring.
"""

from __future__ import annotations

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    """Return ISO 639-1 language code for the given text. Defaults to 'en'."""
    if not text or len(text.strip()) < 20:
        return "en"
    try:
        from langdetect import detect, LangDetectException
        code = detect(text)
        return code[:2].lower() if code else "en"
    except Exception as exc:
        logger.warning("Language detection failed: %s", exc)
        return "en"


# ---------------------------------------------------------------------------
# Topic Tagging  (RAKE-NLTK)
# ---------------------------------------------------------------------------

def extract_topic_tags(text: str, max_tags: int = 10) -> List[str]:
    """
    Extract key topic phrases from text using RAKE-NLTK.
    Falls back to simple frequency-based method if RAKE is unavailable
    (e.g. NumPy/SciPy version incompatibility in the host environment).
    """
    if not text or len(text.strip()) < 50:
        return []
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from rake_nltk import Rake
        import nltk
        # Ensure required NLTK data is present silently
        for pkg in ("stopwords", "punkt", "punkt_tab"):
            try:
                nltk.data.find(f"tokenizers/{pkg}" if pkg.startswith("punkt") else f"corpora/{pkg}")
            except LookupError:
                nltk.download(pkg, quiet=True)

        r = Rake(min_length=1, max_length=4)
        r.extract_keywords_from_text(text[:5000])  # cap input for speed
        phrases = r.get_ranked_phrases()[:max_tags]
        # Filter noise: keep only alphabetic phrases of reasonable length
        cleaned = [p for p in phrases if re.match(r"^[a-zA-Z\s\-]+$", p) and 3 <= len(p) <= 50]
        return cleaned[:max_tags]
    except Exception:
        # Silently fall back — common when scipy/numpy have version conflicts
        return _simple_keyword_extract(text, max_tags)


def _simple_keyword_extract(text: str, max_tags: int = 10) -> List[str]:
    """Frequency-based keyword fallback."""
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    stopwords = {
        "this", "that", "with", "from", "they", "have", "been", "were",
        "their", "said", "also", "more", "will", "into", "than", "then",
        "some", "what", "when", "which", "would", "about", "after", "before"
    }
    freq: dict[str, int] = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq, key=lambda w: freq[w], reverse=True)
    return sorted_words[:max_tags]


# ---------------------------------------------------------------------------
# Text Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, max_words: int = 300) -> List[str]:
    """
    Split text into chunks at paragraph boundaries, keeping each chunk
    under `max_words` words. Returns list of non-empty string chunks.
    """
    if not text:
        return []

    # Split by double newline (paragraph), fallback to single newline
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_word_count = 0

    for para in paragraphs:
        word_count = len(para.split())
        if current_word_count + word_count > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0
        current_chunk.append(para)
        current_word_count += word_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c for c in chunks if c]


def chunk_transcript(segments: list, max_words: int = 200) -> List[str]:
    """
    Chunk YouTube transcript segments (list of dicts with 'text' key)
    into logical groups by word count.
    """
    chunks: List[str] = []
    current: List[str] = []
    current_words = 0

    for seg in segments:
        text = seg.get("text", "").strip()
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


# ---------------------------------------------------------------------------
# Trust Score
# ---------------------------------------------------------------------------

def compute_trust_score(
    source_type: str,
    author: str,
    published_date: str,
    content_chunks: List[str],
    topic_tags: List[str],
) -> float:
    """
    Heuristic trust score (0.0 – 1.0) based on field completeness and source type.

    Scoring rubric:
      - source_type baseline:  pubmed=0.80, youtube=0.65, blog=0.60
      - +0.05 if author is known
      - +0.05 if published_date is non-empty
      - +0.05 if 3+ content_chunks present
      - +0.05 if 3+ topic_tags extracted
      Score is clamped to [0.0, 1.0].
    """
    baselines = {"pubmed": 0.80, "youtube": 0.65, "blog": 0.60}
    score = baselines.get(source_type, 0.50)

    if author and author.lower() not in ("unknown", ""):
        score += 0.05
    if published_date:
        score += 0.05
    if len(content_chunks) >= 3:
        score += 0.05
    if len(topic_tags) >= 3:
        score += 0.05

    return round(min(max(score, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# HTML Cleaning
# ---------------------------------------------------------------------------

def clean_html(text: str) -> str:
    """Strip residual HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)  # HTML entities
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()
