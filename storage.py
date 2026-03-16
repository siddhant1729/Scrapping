"""
storage.py
----------
Partitioned JSON file storage for scraped documents.
Handles read, dedup-append, write, and schema validation across the three output files.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List

from pydantic import ValidationError
from schema import ScrapedDocument

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).parent / "scraped_data"
FILE_MAP: Dict[str, Path] = {
    "blog":    STORAGE_DIR / "blogs.json",
    "youtube": STORAGE_DIR / "youtube.json",
    "pubmed":  STORAGE_DIR / "pubmed.json",
}


def _ensure_storage():
    """Create scraped_data/ and empty JSON arrays if they don't exist."""
    STORAGE_DIR.mkdir(exist_ok=True)
    for path in FILE_MAP.values():
        if not path.exists():
            path.write_text("[]", encoding="utf-8")


def _load(source_type: str) -> List[dict]:
    """Load existing records from the appropriate JSON file."""
    _ensure_storage()
    path = FILE_MAP[source_type]
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupt JSON in %s — resetting to empty list.", path)
        return []


def _save(source_type: str, records: List[dict]):
    """Write records list back to the appropriate JSON file."""
    path = FILE_MAP[source_type]
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def save_document(doc: ScrapedDocument) -> bool:
    """
    Append a ScrapedDocument to the appropriate partition file.
    Deduplicates by source_url (skips if already present).

    Returns True if saved, False if duplicate.
    """
    source_type = doc.source_type
    records = _load(source_type)

    existing_urls = {r.get("source_url") for r in records}
    if doc.source_url in existing_urls:
        logger.info("Duplicate — skipping: %s", doc.source_url)
        return False

    records.append(doc.model_dump())
    _save(source_type, records)
    logger.info("Saved → %s  [%s]", doc.source_url, source_type)
    return True


def validate_all() -> bool:
    """
    Load every record from all three partition files and validate
    each one against the ScrapedDocument schema.

    Prints a summary and returns True if all pass.
    """
    _ensure_storage()
    total = 0
    errors = 0

    for source_type, path in FILE_MAP.items():
        records = _load(source_type)
        print(f"\n📂  {path.name}  ({len(records)} records)")
        for i, record in enumerate(records):
            try:
                ScrapedDocument(**record)
                print(f"  ✅  [{i+1}] {record.get('source_url', 'N/A')}")
                total += 1
            except ValidationError as exc:
                print(f"  ❌  [{i+1}] {record.get('source_url', 'N/A')}")
                print(f"      {exc}")
                errors += 1
                total += 1

    print(f"\n{'='*50}")
    if errors == 0:
        print(f"✅  All {total} document(s) pass schema validation.")
        return True
    else:
        print(f"❌  {errors}/{total} document(s) failed validation.")
        return False


def get_all_records() -> Dict[str, List[dict]]:
    """Return all records grouped by source type."""
    return {st: _load(st) for st in FILE_MAP}
