# 🕷️ Scraper Engine — Multi-Source Data Harvester

> A modular Python engine that extracts, cleans, and normalises content from **Blogs**, **YouTube**, and **PubMed** into a strictly typed JSON schema — ready for LLM fine-tuning, RAG pipelines, or research analysis.

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-validated-e85d24?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

---

## 📖 Overview

The Scraper Engine is a resilient, multi-ecosystem data pipeline with specialised parsers for each content type. It handles boilerplate removal, automatic topic tagging, language detection, and content chunking to produce high-fidelity structured data from disparate web sources.

**Built for:** LLM fine-tuning datasets · RAG pipelines · Research aggregation · Content analysis

---

## ✨ Features

### Multi-Source Support
| Source | Library | Notes |
|--------|---------|-------|
| 📝 **Blogs** | Newspaper3k + Readability-lxml | Fallback for edge cases |
| 🎥 **YouTube** | yt-dlp + youtube-transcript-api | Metadata & transcript extraction |
| 🔬 **PubMed** | Biopython (Entrez) | Scientific metadata & abstracts |

### Intelligent Processing
- **Deduplication** — prevents duplicate entries based on source URL
- **Topic tagging** — automatic key phrase extraction via RAKE-NLTK
- **Content chunking** — segments long-form text into logical blocks
- **Schema validation** — 100% adherence to strict Pydantic models
- **Language detection** — ISO 639-1 codes with fallback for non-English text

### Resilience
- **Header rotation** — randomised user-agents to avoid blocks
- **Rate limiting** — configurable sleep intervals per source
- **Graceful failures** — per-source error isolation keeps the pipeline running

---

## 🏗️ Architecture

```
main.py  (Entry Point)
    └── pipeline.py  (Dispatcher)
            ├── scraper/blog_scraper.py
            ├── scraper/youtube_scraper.py
            └── scraper/pubmed_scraper.py
                        │
                        ▼
                    utils/  (Common Logic)
                    ├── tagging.py
                    ├── chunking.py
                    └── helpers.py
                        │
                        ▼
                    scoring/  (Trust Engine)
                    ├── trust_score.py
                    └── trusted_orgs.json
                        │
                        ▼
                    schema.py + storage.py
```

---

## 🛠️ Installation

**1. Navigate to the project directory**
```cmd
cd Scrapping
```

**2. Install dependencies**
```cmd
pip install -r requirements.txt
```

---

## ⚡ Usage

**Run via Python:**
```cmd
python main.py
```

**Or use the one-click Windows batch script:**
```cmd
run.bat
```

---

## 📊 Data Schema

All extracted records conform to this canonical structure:

| Field | Type | Description |
|-------|------|-------------|
| `source_url` | `string` | Canonical URL or reference ID |
| `source_type` | `enum` | One of `blog`, `youtube`, `pubmed` |
| `author` | `string` | Author name or channel title |
| `published_date` | `string` | ISO-8601 formatted date |
| `language` | `string` | ISO 639-1 language code |
| `topic_tags` | `array` | Extracted topic keywords |
| `trust_score` | `float` | Heuristic credibility score (0.0 – 1.0) |
| `content_chunks` | `array` | Segmented text content blocks |

---

## 📁 Storage Layout

Scraped data is automatically partitioned into the `scraped_data/` directory:

```
scraped_data/
├── blogs.json
├── youtube.json
├── pubmed.json
└── scraped_data.json     ← unified export (all records)
```

---

## 🔐 Trust Score

Scores are computed by `scoring/trust_score.py` using five weighted factors:

```
Trust Score = f( author_credibility, citation_count, domain_authority, recency, medical_disclaimer )
```

| Factor | Weight | Method |
|--------|--------|--------|
| Domain Authority | **0.30** | Tiered whitelist (`scoring/trusted_orgs.json`) |
| Recency | **0.25** | Exponential decay `e^(−0.3·t)` |
| Author Credibility | **0.20** | Trusted org lookup + multi-author averaging |
| Citation Count | **0.15** | Content depth proxy + 50% spam penalty |
| Medical Safety | **0.10** | Disclaimer keyword detection |

---

## ⚠️ Known Limitations

- **Blog paywalls** — Newspaper3k cannot extract content behind paywalls (e.g. WSJ, FT). Readability falls back to minimal text.
- **YouTube transcripts** — auto-generated captions may contain errors; videos with no captions produce empty `content_chunks`.
- **PubMed rate limits** — without an API key, NCBI caps requests at 3/sec. Bulk PMID scraping will be slow.
- **Citation count** — real citation data (Semantic Scholar, CrossRef) is not implemented; chunk depth is used as a proxy.
- **Region detection** — blog and YouTube `region` is always `null`; geo-detection is out of scope.
- **Non-English text** — RAKE-NLTK performs poorly on non-English content; a simple frequency fallback is used automatically.
- **NumPy/SciPy compatibility** — RAKE-NLTK may crash silently with a NumPy 2.x / SciPy version conflict; the frequency fallback activates automatically.

---

## 🧰 Tech Stack

| Library | Purpose |
|---------|---------|
| `newspaper3k` | Blog content extraction |
| `readability-lxml` | Fallback HTML parser |
| `yt-dlp` | YouTube metadata |
| `youtube-transcript-api` | YouTube transcript extraction |
| `biopython` | PubMed / NCBI Entrez API |
| `pydantic` | Schema validation |
| `rake-nltk` | Topic keyword extraction |
| `langdetect` | Language identification |

---

## 📄 License

MIT — free to use, modify, and distribute.

---

*Built with ❤️ by Siddhant.*
