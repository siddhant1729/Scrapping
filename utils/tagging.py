"""
utils/tagging.py
-----------------
Keyword and topic extraction module.
Uses RAKE (Rapid Automatic Keyword Extraction) with NLTK stopwords.
Called by all parsers to generate topic_tags for the JSON output.

Falls back to a simple frequency-based extractor if RAKE is unavailable
(e.g. NumPy/SciPy version conflicts in Anaconda environments).
"""

import re
import logging

logger = logging.getLogger(__name__)

_STOP_WORDS = {
    "this", "that", "with", "from", "they", "have", "been", "were",
    "their", "said", "also", "more", "will", "into", "than", "then",
    "some", "what", "when", "which", "would", "about", "after", "before",
    "there", "where", "while", "through", "during", "because", "however",
}


def _simple_extract(text: str, max_tags: int = 8) -> list:
    """Frequency-based keyword fallback when RAKE is unavailable."""
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    freq: dict = {}
    for w in words:
        if w not in _STOP_WORDS:
            freq[w] = freq.get(w, 0) + 1
    return sorted(freq, key=lambda x: -freq[x])[:max_tags]


def extract_tags(text: str, max_tags: int = 8) -> list:
    """
    Extract top keyword phrases from text using RAKE-NLTK.
    Returns a list of up to max_tags keyword phrases.
    Returns [] if text is None or empty.
    Falls back to frequency extraction if RAKE/NLTK are unavailable.
    """
    if not text or not text.strip():
        return []
    try:
        import nltk
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
        from rake_nltk import Rake
        rake = Rake()
        rake.extract_keywords_from_text(text)
        phrases = rake.get_ranked_phrases()
        cleaned = []
        # Filter for placeholders, dividers, and junk
        junk_patterns = [
            r'-{3,}', r'_{3,}', r'\.{3,}', # Dividers
            r'subscribe', r'click here', r'follow us', # Call to action
            r'http[s]?://', r'www\.', # URLs
            r'timeline', r'timestamp', # Structural words
        ]
        
        for p in phrases:
            p = p.lower().strip()
            # Allow alphanumeric + basic punctuation, but length 4-50
            if re.match(r'^[a-z0-9\s\-\.\']+$', p) and 4 <= len(p) <= 50:
                # Skip if matches any junk patterns
                if any(re.search(pat, p) for pat in junk_patterns):
                    continue
                # Skip if too many non-alphanumeric chars (e.g. "---")
                if len(re.findall(r'[^a-zA-Z0-9\s]', p)) > 2:
                    continue
                if p not in cleaned:
                    cleaned.append(p)

        if not cleaned and text.strip():
            logger.debug("RAKE found no suitable tags; falling back to simple extraction.")
            return _simple_extract(text, max_tags)

        return cleaned[:max_tags]
    except Exception as exc:
        logger.debug("Topic extraction error: %s — using simple fallback.", exc)
        return _simple_extract(text, max_tags)
