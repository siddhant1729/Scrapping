"""
scraper/pubmed_scraper.py
--------------------------
Extracts structured metadata and abstract from PubMed records using Biopython Entrez.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional
from xml.etree import ElementTree as ET

from schema import ScrapedDocument
from utils.tagging import extract_tags
from utils.chunking import chunk_text
from utils.helpers import detect_language
from scoring.trust_score import TrustScoreEngine

logger = logging.getLogger(__name__)

_trust_engine = TrustScoreEngine()

ENTREZ_EMAIL = "scraper@example.com"
NCBI_API_KEY: Optional[str] = None
REQUEST_INTERVAL = 0.4


def _configure_entrez():
    from Bio import Entrez
    Entrez.email = ENTREZ_EMAIL
    if NCBI_API_KEY:
        Entrez.api_key = NCBI_API_KEY


def _fetch_pubmed_xml(pmid: str) -> str:
    """Fetch raw XML from NCBI Entrez efetch for a given PMID."""
    from Bio import Entrez
    _configure_entrez()
    time.sleep(REQUEST_INTERVAL)
    handle = Entrez.efetch(db="pubmed", id=pmid, rettype="xml", retmode="xml")
    xml_data = handle.read()
    handle.close()
    return xml_data if isinstance(xml_data, str) else xml_data.decode("utf-8")


def _parse_xml(xml_data: str) -> dict:
    """Parse PubMed XML to extract title, abstract, authors, journal, pub_date."""
    root = ET.fromstring(xml_data)
    article = root.find(".//PubmedArticle")
    if article is None:
        raise ValueError("No PubmedArticle found in XML response.")

    title_el = article.find(".//ArticleTitle")
    title = "".join(title_el.itertext()) if title_el is not None else ""

    abstract_texts = article.findall(".//AbstractText")
    if abstract_texts:
        parts = []
        for ab in abstract_texts:
            label = ab.get("Label", "")
            text = "".join(ab.itertext()).strip()
            parts.append(f"{label}: {text}" if label else text)
        abstract = "\n\n".join(parts)
    else:
        abstract = ""

    authors: List[str] = []
    for author_el in article.findall(".//Author"):
        last = author_el.findtext("LastName", "")
        fore = author_el.findtext("ForeName", "")
        if last:
            authors.append(f"{fore} {last}".strip())

    journal_el = article.find(".//Journal/Title")
    journal = journal_el.text if journal_el is not None else ""

    pub_year = article.findtext(".//PubDate/Year", "")
    pub_month = article.findtext(".//PubDate/Month", "")
    pub_day = article.findtext(".//PubDate/Day", "")

    pub_date = pub_year
    if pub_year and pub_month:
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
        }
        month_num = month_map.get(pub_month, pub_month.zfill(2))
        pub_date = f"{pub_year}-{month_num}"
        if pub_day:
            pub_date += f"-{pub_day.zfill(2)}"

    return {"title": title, "abstract": abstract, "authors": authors,
            "journal": journal, "pub_date": pub_date}


def parse_pubmed(pmid: str) -> ScrapedDocument:
    """Fetch and parse a PubMed article by PMID."""
    pmid = str(pmid).strip()
    logger.info("PubMed scraper → PMID %s", pmid)
    canonical_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    try:
        xml_data = _fetch_pubmed_xml(pmid)
        meta = _parse_xml(xml_data)
    except Exception as exc:
        logger.error("PubMed fetch/parse failed for PMID %s: %s", pmid, exc)
        return ScrapedDocument(
            source_url=canonical_url, source_type="pubmed",
            author="Unknown", published_date="", language="en",
            topic_tags=[], trust_score=0.4, content_chunks=[],
        )

    abstract = meta.get("abstract", "")
    authors = meta.get("authors", [])
    author_str = ", ".join(authors) if authors else "Unknown"
    journal = meta.get("journal", "")
    pub_date = meta.get("pub_date", "")

    language = detect_language(abstract)
    topic_tags = extract_tags(abstract)
    content_chunks = chunk_text(abstract)

    trust_score = _trust_engine.compute(
        source_url=canonical_url,
        source_type="pubmed",
        author=author_str,
        published_date=pub_date,
        content_chunks=content_chunks,
        topic_tags=topic_tags,
        raw_text=abstract,
    )

    return ScrapedDocument(
        source_url=canonical_url,
        source_type="pubmed",
        author=author_str,
        published_date=pub_date,
        language=language,
        region=journal if journal else None,
        topic_tags=topic_tags,
        trust_score=trust_score,
        content_chunks=content_chunks,
    )
