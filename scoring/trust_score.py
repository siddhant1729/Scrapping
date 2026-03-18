"""
scoring/trust_score.py
-----------------------
TrustScoreEngine: A mathematical evaluation engine that assigns a credibility
rating (0.0 to 1.0) to every piece of scraped content.

Trust Score Formula (per assignment spec):
    TS = f(author_credibility, citation_count, domain_authority,
           recency, medical_disclaimer_presence)

Implemented as weighted linear combination:
    TS = Σ(w_i · s_i)

Factors and weights (must sum = 1.0):
    ① Domain Authority     w=0.30
    ② Recency              w=0.25
    ③ Author Credibility   w=0.20
    ④ Citation Count       w=0.15  (proxy: content depth + spam guard)
    ⑤ Medical Disclaimer Presence  w=0.10
"""

from __future__ import annotations

import json
import logging
import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Path to trusted_orgs.json seated next to this file
_TRUSTED_ORGS_PATH = Path(__file__).with_name("trusted_orgs.json")

# ---------------------------------------------------------------------------
# Factor Weights  (must sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHTS = {
    "domain_authority":  0.30,
    "recency":           0.25,
    "author_credibility": 0.20,
    "citation_count":    0.15,
    "medical_disclaimer_presence": 0.10,
}

# Recency decay constant (λ). At λ=0.3:
#   1 year → 0.74,   3 years → 0.41,   5 years → 0.22,   10 years → 0.05
LAMBDA = 0.3

# Keyword-stuffing threshold: if tag_ratio > this → 50% quality penalty
TAG_SPAM_RATIO = 0.03

# Disclaimer phrases for medical safety check
DISCLAIMER_PHRASES = [
    "not medical advice", "not a substitute for professional",
    "consult a physician", "consult your doctor", "consult a professional",
    "consult a healthcare", "seek medical advice", "for informational purposes only",
    "talk to your doctor", "this is not intended as medical",
]


class TrustScoreEngine:
    """
    Stateless engine that computes a trust score from document metadata.
    Load trusted_orgs.json once at instantiation for performance.
    """

    def __init__(self, orgs_path: Path = _TRUSTED_ORGS_PATH) -> None:
        try:
            with open(orgs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._high_domains: set[str] = set(data["trusted_domains"]["high"])
            self._medium_domains: set[str] = set(data["trusted_domains"]["medium"])
            self._trusted_authors: list[str] = [a.lower() for a in data["trusted_authors"]]
            self._trusted_orgs: list[str] = [o.lower() for o in data["trusted_orgs"]]
        except Exception as exc:
            logger.warning("Could not load trusted_orgs.json: %s — using defaults.", exc)
            self._high_domains = {"pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "nature.com"}
            self._medium_domains = {"medium.com", "blog.google"}
            self._trusted_authors = ["google", "openai", "nih"]
            self._trusted_orgs = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(
        self,
        source_url: str,
        source_type: str,
        author: str,
        published_date: str,
        content_chunks: List[str],
        topic_tags: List[str],
        raw_text: str = "",
    ) -> float:
        """
        Compute and return a trust score in [0.0, 1.0].

        Parameters
        ----------
        source_url      : Canonical URL of the document.
        source_type     : 'blog', 'youtube', or 'pubmed'.
        author          : Author or channel name (comma-separated if multiple).
        published_date  : ISO-8601 date string, or '' if unknown.
        content_chunks  : List of text segments.
        topic_tags      : Extracted keyword tags.
        raw_text        : Full body text (used for disclaimer check).
        """
        s = {
            "domain_authority":   self._score_domain(source_url, source_type),
            "recency":            self._score_recency(published_date),
            "author_credibility": self._score_author(author, source_url),
            "citation_count":     self._score_citation_proxy(content_chunks, topic_tags, source_type),
            "medical_disclaimer_presence": self._score_medical_disclaimer(source_type, raw_text)
        }

        ts = sum(WEIGHTS[k] * s[k] for k in WEIGHTS)
        result = round(min(max(ts, 0.0), 1.0), 4)

        logger.debug(
            "TrustScore for %s | domain=%.2f recency=%.2f author=%.2f "
            "citation=%.2f medical_disclaimer=%.2f → TS=%.4f",
            source_url, s["domain_authority"], s["recency"],
            s["author_credibility"], s["citation_count"], s["medical_disclaimer_presence"], result,
        )
        return result

    # ------------------------------------------------------------------
    # Factor ①: Domain Authority  (w=0.30)
    # ------------------------------------------------------------------

    def _score_domain(self, url: str, source_type: str) -> float:
        """
        Tiered domain score.
        PubMed always = 1.0 (authoritative by definition).
        High-trust domain = 1.0, Medium = 0.5, Unknown = 0.15.
        """
        if source_type == "pubmed":
            return 1.0

        # Extract base domain from URL
        domain = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()

        # Walk up subdomain hierarchy: e.g. news.bbc.co.uk → bbc.co.uk → bbc.co → co.uk
        parts = domain.split(".")
        for i in range(len(parts)):
            candidate = ".".join(parts[i:])
            if candidate in self._high_domains:
                return 1.0
            if candidate in self._medium_domains:
                return 0.5

        return 0.15  # Unknown / unverified domain

    # ------------------------------------------------------------------
    # Factor ②: Recency  (w=0.25)
    # ------------------------------------------------------------------

    def _score_recency(self, published_date: str) -> float:
        """
        Exponential decay: s = e^(-λ·t)  where t = age in years.
        Missing date: stale penalty = 0.4.
        """
        if not published_date:
            return 0.4  # Missing date → safe stale penalty

        try:
            pub = datetime.strptime(published_date[:10], "%Y-%m-%d").date()
        except ValueError:
            try:
                pub = date(int(published_date[:4]), 1, 1)  # Year-only fallback
            except Exception:
                return 0.4

        age_years = (date.today() - pub).days / 365.25
        age_years = max(age_years, 0.0)  # Not negative for future dates
        return round(math.exp(-LAMBDA * age_years), 4)

    # ------------------------------------------------------------------
    # Factor ③: Author Credibility  (w=0.20)
    # ------------------------------------------------------------------

    def _score_author(self, author: str, url: str) -> float:
        """
        Match author against trusted_orgs.json.
        Handles multiple authors (comma-separated): averages their scores.

        - Trusted org match → 1.0
        - Named (not matched) → 0.7
        - Missing on high-trust domain → 0.65
        - Missing on unknown domain → 0.3
        """
        # --- Handle multiple authors (assignment spec: average credibility) ---
        authors = [a.strip() for a in (author or "").split(",") if a.strip()]
        if len(authors) > 1:
            scores = [self._score_single_author(a, url) for a in authors]
            return round(sum(scores) / len(scores), 4)
        return self._score_single_author(author, url)

    def _score_single_author(self, author: str, url: str) -> float:
        """Score one individual author string."""
        author_lower = (author or "").lower().strip()
        unknown_aliases = {"", "unknown", "n/a", "none"}

        for trusted in self._trusted_orgs + self._trusted_authors:
            if trusted in author_lower:
                return 1.0

        if author_lower not in unknown_aliases:
            return 0.7

        domain = re.sub(r"^https?://(www\.)?" , "", url).split("/")[0].lower()
        parts = domain.split(".")
        for i in range(len(parts)):
            if ".".join(parts[i:]) in self._high_domains:
                return 0.65
        return 0.3

    # ------------------------------------------------------------------
    # Factor ④: Citation Count (proxy)  (w=0.15)
    # ------------------------------------------------------------------

    def _score_citation_proxy(
        self, content_chunks: List[str], topic_tags: List[str], source_type: str
    ) -> float:
        """
        Proxy for citation_count using content depth and spam detection.

        PubMed: always 1.0 (peer-reviewed = inherently cited).
        Others: score by chunk count, penalise keyword stuffing.

        Rubric:
          0 chunks  → 0.10
          1 chunk   → 0.40
          2 chunks  → 0.65
          3–4 chunks → 0.85
          5+ chunks → 1.00
        Keyword-stuffing (tag_ratio > 0.03) → ×0.5 penalty.
        """
        if source_type == "pubmed":
            return 1.0  # Peer-reviewed papers are by definition cited

        n = len(content_chunks)
        if n == 0:
            base = 0.10
        elif n == 1:
            base = 0.40
        elif n == 2:
            base = 0.65
        elif n < 5:
            base = 0.85
        else:
            base = 1.00

        total_words = sum(len(c.split()) for c in content_chunks)
        if total_words > 0 and (len(topic_tags) / total_words) > TAG_SPAM_RATIO:
            logger.debug("Keyword-stuffing detected — applying 50%% citation penalty.")
            base *= 0.5

        return round(base, 4)

    # ------------------------------------------------------------------
    # Factor ⑤: Medical Disclaimer Presence  (w=0.10)
    # ------------------------------------------------------------------

    def _score_medical_disclaimer(self, source_type: str, raw_text: str) -> float:
        """
        Boolean check for disclaimer phrases.
        PubMed: always 1.0 (peer-reviewed = inherently safe).
        Blog/YouTube: 1.0 if disclaimer found, 0.0 otherwise.
        """
        if source_type == "pubmed":
            return 1.0

        text_lower = (raw_text or "").lower()
        for phrase in DISCLAIMER_PHRASES:
            if phrase in text_lower:
                return 1.0
        return 0.0
