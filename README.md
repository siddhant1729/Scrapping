# 🕷️ Scraper Engine: Multi-Source Data Harvester

![Scraper Hero Banner](./assets/hero_banner.png)

A robust, multi-ecosystem scraping engine designed to extract, clean, and normalize content from disparate sources into a strictly typed JSON schema. Targeted towards **Blogs**, **YouTube**, and **PubMed**.

## 🚀 Overview

The Scraper Engine is a modular Python system that utilizes specialized parsers for different content types. It handles boilerplate removal, automatic topic tagging, language detection, and content chunking to provide high-fidelity data for downstream processing (e.g., LLM fine-tuning, RAG pipelines, or research analysis).

## ✨ Key Features

- **Multi-Source Support**:
  - 📝 **Blogs**: High-fidelity text extraction using Newspaper3k with Readability-lxml fallback.
  - 🎥 **YouTube**: Metadata and transcript extraction via `yt-dlp` and `youtube-transcript-api`.
  - 🔬 **PubMed**: Scientific literature metadata and abstract extraction via Biopython (Entrez).
- **Intelligent Processing**:
  - **Deduplication**: Prevents duplicate entries based on Source URL.
  - **Topic Tagging**: Automatic extraction of key phrases using RAKE-NLTK.
  - **Content Chunking**: Segmenting long-form text into logical segments.
  - **Schema Validation**: 100% adherence to strict Pydantic schemas.
- **Resilience**:
  - **Anti-Scraping**: Header rotation with randomized User-Agents.
  - **Rate Limiting**: Configurable sleep intervals to respect source policies.
  - **Graceful Failures**: Error isolation per source ensures the pipeline continues even if one target fails.

## 🏗️ Architecture

```mermaid
graph TD
    A[main.py: Entry Point] --> B[pipeline.py: Dispatcher]
    B --> C1[parsers/blog_parser.py]
    B --> C2[parsers/youtube_parser.py]
    B --> C3[parsers/pubmed_parser.py]
    
    C1 --> D[utils.py: Common Tools]
    C2 --> D
    C3 --> D
    
    D --> E[schema.py: Data Model]
    E --> F[storage.py: JSON Storage]
    
    subgraph "Processing Logic"
    D -.-> D1[Language Detection]
    D -.-> D2[Topic Tagging]
    D -.-> D3[Text Chunking]
    D -.-> D4[Trust Scoring]
    end
```

## 🛠️ Installation

1. **Clone the repository**:
   ```cmd
   cd "C:\Users\shaur\OneDrive\Desktop\Scrapper"
   ```

2. **Install Dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

## ⚡ Usage

Run the scraper using the main entry point:

```cmd
python main.py
```

Or use the provided one-click batch script on Windows:
```cmd
run.bat
```

## 📊 Data Schema

All extracted data follows this canonical structure:

| Field | Type | Description |
|---|---|---|
| `source_url` | `string` | The canonical URL or reference ID. |
| `source_type` | `enum` | one of `blog`, `youtube`, `pubmed`. |
| `author` | `string` | Author name or Channel title. |
| `published_date`| `string` | ISO-8601 formatted date. |
| `language` | `string` | ISO 639-1 language code. |
| `topic_tags` | `array` | Extracted topic keywords. |
| `trust_score` | `float` | Heuristic score (0.0 - 1.0). |
| `content_chunks`| `array` | Segmented text content. |

## 📁 Storage Strategy

Data is automatically partitioned into the `scraped_data/` directory:
- `scraped_data/blogs.json`
- `scraped_data/youtube.json`
- `scraped_data/pubmed.json`
- `scraped_data/scraped_data.json` ← unified export (all 6 records)

## 🔐 Trust Score Design

Scores are computed by `scoring/trust_score.py` using 5 weighted factors that match the assignment formula:

```
Trust Score = f(author_credibility, citation_count, domain_authority, recency, medical_disclaimer_presence)
```

| Factor | Weight | Method |
|---|---|---|
| Domain Authority | 0.30 | Tiered whitelist (`scoring/trusted_orgs.json`) |
| Recency | 0.25 | Exponential decay `e^(-0.3·t)` |
| Author Credibility | 0.20 | Trusted org lookup + multi-author averaging |
| Citation Count | 0.15 | Content depth proxy + 50% spam penalty |
| Medical Safety | 0.10 | Disclaimer keyword detection |

## ⚠️ Limitations

- **Blog paywalls**: Newspaper3k cannot extract content behind paywalls (e.g. WSJ, FT). Readability falls back to minimal text.
- **YouTube transcripts**: Auto-generated captions may contain errors; some videos have no captions at all — `content_chunks` will be empty for those.
- **PubMed rate limits**: Without an API key, requests are capped at 3/sec by NCBI. Bulk scraping of many PMIDs will be slow.
- **Citation count**: A real citation count (e.g. from Semantic Scholar or CrossRef) is not implemented — chunk depth is used as a proxy.
- **Region detection**: Blog and YouTube `region` is always `null`. Geo-detection would require IP or metadata analysis beyond the current scope.
- **Language support**: RAKE-NLTK performs poorly on non-English text; the simple frequency fallback is used for those cases.
- **NumPy/SciPy compatibility**: RAKE-NLTK may crash silently if your environment has a NumPy 2.x/SciPy version conflict — the simple fallback activates automatically.

---

Built with ❤️ by Antigravity for Siddhant.
