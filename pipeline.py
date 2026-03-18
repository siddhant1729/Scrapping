"""
pipeline.py
-----------
Central dispatcher that routes URLs/IDs to the correct parser
and returns validated ScrapedDocument objects.
"""

from __future__ import annotations

import logging
from typing import Literal

from schema import ScrapedDocument

logger = logging.getLogger(__name__)

SOURCE_TYPE = Literal["blog", "youtube", "pubmed"]


def process(
    url_or_id: str,
    source_type: SOURCE_TYPE,
    **kwargs,
) -> ScrapedDocument:
    """
    Route a URL or identifier to the appropriate scraper.

    Parameters
    ----------
    url_or_id : str
        - For blogs   : full URL (https://...)
        - For youtube : full YouTube URL or video ID
        - For pubmed  : PMID (numeric string)
    source_type : str
        One of "blog", "youtube", "pubmed".
    **kwargs :
        Additional keyword arguments forwarded to the scraper.

    Returns
    -------
    ScrapedDocument
        A validated, schema-compliant document.
    """
    logger.info("Pipeline → source_type=%s  target=%s", source_type, url_or_id)

    if source_type == "blog":
        from scraper.blog_scraper import parse_blog
        return parse_blog(url_or_id, **kwargs)

    elif source_type == "youtube":
        from scraper.youtube_scraper import parse_youtube
        return parse_youtube(url_or_id, **kwargs)

    elif source_type == "pubmed":
        from scraper.pubmed_scraper import parse_pubmed
        return parse_pubmed(url_or_id, **kwargs)

    else:
        raise ValueError(
            f"Unknown source_type: {source_type!r}. Must be 'blog', 'youtube', or 'pubmed'."
        )
