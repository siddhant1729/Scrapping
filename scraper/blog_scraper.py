"""
scraper/blog_scraper.py
------------------------
Extracts article content from blog URLs using Newspaper3k with readability-lxml fallback.
Rotates User-Agent headers to reduce anti-scraping blocks.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import requests

from schema import ScrapedDocument
from utils.tagging import extract_tags
from utils.chunking import chunk_text
from utils.helpers import get_request_headers, clean_text, detect_language
from scoring.trust_score import TrustScoreEngine

logger = logging.getLogger(__name__)

_trust_engine = TrustScoreEngine()


# ---------------------------------------------------------------------------
# Primary extractor: Newspaper3k
# ---------------------------------------------------------------------------

def _extract_with_newspaper(url: str) -> dict:
    """Returns dict: {title, author, date, text}. Raises on failure."""
    from newspaper import Article
    import nltk
    
    # Ensure Newspaper3k has the basic tokenizer data
    nltk.download('punkt', quiet=True)

    headers = get_request_headers()
    article = Article(url, request_timeout=20)
    
    # Download with custom headers to prevent blocking
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    
    article.set_html(resp.text)
    article.parse()

    author = ", ".join(article.authors) if article.authors else "Unknown"
    date_str = ""
    if article.publish_date:
        date_str = article.publish_date.strftime("%Y-%m-%d")

    return {
        "title": article.title or "",
        "author": author,
        "published_date": date_str,
        "text": article.text or "",
    }


# ---------------------------------------------------------------------------
# Fallback extractor: readability-lxml
# ---------------------------------------------------------------------------

def _extract_with_readability(url: str) -> dict:
    """Returns dict: {title, author, date, text}."""
    from readability import Document

    resp = requests.get(url, headers=get_request_headers(), timeout=20)
    resp.raise_for_status()

    doc = Document(resp.text)
    text = clean_text(doc.summary())

    return {
        "title": doc.title() or "",
        "author": "Unknown",
        "published_date": "",
        "text": text,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_blog(url: str, sleep_sec: float = 1.5) -> ScrapedDocument:
    """
    Scrape a blog URL and return a validated ScrapedDocument.

    Parameters
    ----------
    url : str       The blog post URL.
    sleep_sec : float  Polite delay before request (seconds).
    """
    logger.info("Blog scraper → %s", url)
    time.sleep(sleep_sec)

    data: Optional[dict] = None

    try:
        data = _extract_with_newspaper(url)
        if len(data.get("text", "")) < 100:
            raise ValueError("Newspaper3k returned insufficient text; trying fallback.")
    except Exception as exc:
        logger.warning("Newspaper3k failed for %s: %s — falling back to readability", url, exc)
        try:
            data = _extract_with_readability(url)
        except Exception as exc2:
            logger.error("readability fallback also failed for %s: %s", url, exc2)
            data = {"title": "", "author": "Unknown", "published_date": "", "text": ""}

    text = data.get("text", "")
    author = data.get("author", "Unknown") or "Unknown"
    published_date = data.get("published_date", "")

    language = detect_language(text)
    topic_tags = extract_tags(text)
    content_chunks = chunk_text(text)

    trust_score = _trust_engine.compute(
        source_url=url,
        source_type="blog",
        author=author,
        published_date=published_date,
        content_chunks=content_chunks,
        topic_tags=topic_tags,
        raw_text=text,
    )

    return ScrapedDocument(
        source_url=url,
        source_type="blog",
        author=author,
        published_date=published_date,
        language=language,
        region=None,
        topic_tags=topic_tags,
        trust_score=trust_score,
        content_chunks=content_chunks,
    )
