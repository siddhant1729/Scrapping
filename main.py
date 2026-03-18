"""
main.py
-------
Entry point for the multi-source scraping engine.
Processes 6 pre-defined sources (3 blogs, 2 YouTube, 1 PubMed) and
stores results into partitioned JSON files under scraped_data/.

Usage:
    python main.py
"""

from __future__ import annotations

import logging
import sys
from typing import List, Tuple

from tqdm import tqdm

from pipeline import process
from schema import ScrapedDocument
from storage import save_document, validate_all, export_unified_json

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Source definitions:  (type, url_or_id, display_label)
# ---------------------------------------------------------------------------
SOURCES: List[Tuple[str, str, str]] = [
    # --- Blogs (3) ---
    (
        "blog",
        "https://openai.com/index/openai-o1-preview-now-available-in-chatgpt-plus-and-team/",
        "OpenAI Blog: O1 Model Announcement",
    ),
    (
        "blog",
        "https://news.mit.edu/2024/mit-researchers-develop-new-way-measure-uncertainty-ai-1219",
        "MIT News: AI Uncertainty Measurement",
    ),
    (
        "blog",
        "https://blog.google/technology/ai/google-gemini-ai/",
        "Google Gemini Blog Post",
    ),
    # --- YouTube (2) ---
    (
        "youtube",
        "https://www.youtube.com/watch?v=aircAruvnKk",
        "3Blue1Brown: Neural Networks",
    ),
    (
        "youtube",
        "https://www.youtube.com/watch?v=ukzFI9rgwfU",
        "Veritasium: How AI Sees",
    ),
    # --- PubMed (1) ---
    (
        "pubmed",
        "39776398",
        "PubMed PMID 39776398",
    ),
]


def run():
    print("\n" + "=" * 60)
    print("  🕷️   Multi-Source Scraping Engine")
    print("=" * 60)
    print(f"  Sources to process: {len(SOURCES)}")
    print("=" * 60 + "\n")

    results: List[ScrapedDocument] = []
    failed: List[Tuple[str, str, str]] = []

    for source_type, target, label in tqdm(SOURCES, desc="Scraping", unit="source"):
        print(f"\n▶  [{source_type.upper()}]  {label}")
        print(f"   Target: {target}")
        try:
            doc = process(target, source_type)
            saved = save_document(doc)
            status = "saved" if saved else "duplicate (skipped)"
            print(f"   ✅  Done — {len(doc.content_chunks)} chunks, "
                  f"{len(doc.topic_tags)} tags, "
                  f"trust={doc.trust_score:.2f}  [{status}]")
            results.append(doc)
        except Exception as exc:
            logger.error("FAILED: %s (%s) — %s", label, target, exc, exc_info=True)
            print(f"   ❌  Failed: {exc}")
            failed.append((source_type, target, label))

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  📊  Run Summary")
    print("=" * 60)
    print(f"  ✅  Succeeded : {len(results)}/{len(SOURCES)}")
    print(f"  ❌  Failed    : {len(failed)}/{len(SOURCES)}")

    if failed:
        print("\n  Failed sources:")
        for ft, fu, fl in failed:
            print(f"    • [{ft}] {fl} → {fu}")

    # ---------------------------------------------------------------------------
    # Schema Validation
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  🔍  Schema Validation")
    print("=" * 60)
    all_valid = validate_all()

    print("\n" + "=" * 60)
    if all_valid:
        print("  🎉  All done! Output stored in scraped_data/")
    else:
        print("  ⚠️   Completed with validation errors. Check scraper.log for details.")
    print("=" * 60)

    # ---------------------------------------------------------------------------
    # Unified Export
    # ---------------------------------------------------------------------------
    unified = export_unified_json()
    print(f"\n  📦  Unified JSON → {unified}")
    print("=" * 60 + "\n")

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(run())
