"""
parsers/blog_parser.py
----------------------
Extracts article content from blog URLs using Newspaper3k with readability-lxml fallback.
Rotates User-Agent headers to reduce anti-scraping blocks.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional

import requests

from schema import ScrapedDocument
from utils import chunk_text, detect_language, extract_topic_tags, compute_trust_score, clean_html

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# User-Agent pool for header rotation
# ---------------------------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]


def _random_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ---------------------------------------------------------------------------
# Primary extractor: Newspaper3k
# ---------------------------------------------------------------------------

def _extract_with_newspaper(url: str) -> dict:
    """
    Returns dict: {title, author, date, text}
    Raises on failure.
    """
    from newspaper import Article

    article = Article(url, request_timeout=20)
    article.set_html(
        requests.get(url, headers=_random_headers(), timeout=20).text
    )
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
    """
    Returns dict: {title, author, date, text}
    """
    from readability import Document

    resp = requests.get(url, headers=_random_headers(), timeout=20)
    resp.raise_for_status()

    doc = Document(resp.text)
    raw_content = doc.summary()
    text = clean_html(raw_content)

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
    url : str
        The blog post URL.
    sleep_sec : float
        Polite delay before request (seconds).
    """
    logger.info("Blog parser → %s", url)
    time.sleep(sleep_sec)

    data: Optional[dict] = None

    # Try Newspaper3k first
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
    topic_tags = extract_topic_tags(text)
    content_chunks = chunk_text(text)

    trust_score = compute_trust_score(
        source_type="blog",
        author=author,
        published_date=published_date,
        content_chunks=content_chunks,
        topic_tags=topic_tags,
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
