"""
utils/helpers.py
-----------------
Shared helper utilities used by all parsers.
Includes: user-agent rotation, text cleaning, date parsing, language detection.
"""

import random
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# User-Agent Rotation
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 Version/17.3 Safari/605.1.15",
]


def get_random_user_agent() -> str:
    """Return a random browser User-Agent string."""
    return random.choice(USER_AGENTS)


def get_request_headers() -> dict:
    """Return a full set of browser-like request headers."""
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ---------------------------------------------------------------------------
# Text Cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Strip HTML tags, extra whitespace, and non-printable characters."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)   # Remove HTML tags
    text = re.sub(r'\s+', ' ', text)       # Collapse whitespace
    return text.strip()

# Alias for backwards compatibility
clean_html = clean_text


# ---------------------------------------------------------------------------
# Date Parsing
# ---------------------------------------------------------------------------

def parse_date(date_str: str) -> str:
    """
    Attempt to parse any date string into ISO 8601 format (YYYY-MM-DD).
    Returns empty string on failure.
    """
    if not date_str:
        return ""
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y",
        "%B %d, %Y", "%b %d, %Y", "%Y/%m/%d",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str.strip()


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
# Safe Dict Access
# ---------------------------------------------------------------------------

def safe_get(dict_obj: dict, key: str, default="") -> str:
    """Safely retrieve a key from a dict without raising KeyError."""
    if not dict_obj or not isinstance(dict_obj, dict):
        return default
    return dict_obj.get(key, default)
