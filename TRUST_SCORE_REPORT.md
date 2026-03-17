# Trust Score System — Technical Report

## Section 1: Scraping Strategy

The multi-source scraping engine is designed for high-fidelity extraction from three distinct ecosystems:

- **Blogs (Newspaper3k + Readability)**: We utilize `newspaper3k` for its specialized ability to identify and extract the "clean" body text of articles while discarding headers, footers, and advertisements. A fallback to `readability-lxml` ensures that even non-standard blogs are processed with high accuracy.
- **YouTube (yt-dlp + youtube-transcript-api)**: To capture the depth of video content, we extract both high-level metadata (via `yt-dlp`) and the full text transcript. This allows the trust engine to evaluate the actual verbal content of the video rather than just the title/description.
- **PubMed (Biopython Entrez)**: We use the official NCBI Entrez API to fetch structured XML. This provides scientific-grade accuracy for authors, journal identifiers, and publication dates, forming the "gold standard" for our trust evaluation.

---

## Section 2: Topic Tagging Method

Automatic topic generation is performed via a hybrid NLP approach in `utils.py`:

1. **RAKE-NLTK (Primary)**: We use the Rapid Automatic Keyword Extraction (RAKE) algorithm to identify candidate phrases based on the co-occurrence of words. This identifies technical terms (e.g., "Machine Learning") rather than just single words.
2. **Frequency Fallback**: To ensure resilience (especially during NumPy/SciPy version conflicts), we implement a fallback frequency analyzer. This ensures that the scraper remains functional even in restricted environments.
3. **Filtering**: All tags are cross-referenced against a list of common stop-words and normalized to ensure the output is clean and relevant for the `topic_tags` JSON field.

---

## Section 3: Trust Score Algorithm

### 3.1 The Core Formula

The Trust Score (TS) is a **weighted linear combination of five normalized factors**, ensuring a transparent and objective credibility rating in the range $[0.0, 1.0]$:

$$TS = \sum (w_i \cdot s_i)$$

| Factor | Weight ($w_i$) | Rationale |
|---|---|---|
| Domain Authority | **0.30** | Publisher reputation is the strongest proxy for reliability. |
| Recency | **0.25** | Information decay is critical, especially in tech/medicine. |
| Author Credibility | **0.20** | Named, verified responsibility for content. |
| Citation Count | **0.15** | Depth of content and structural substantive signals. |
| Medical Safety | **0.10** | Presence of disclaimers for ethical/regulatory safety. |

### 3.2 Factor Definitions & Normalization

- **Domain Authority**: Tiered lookup (High=1.0, Med=0.5, Low=0.15). PubMed is hard-coded as 1.0.
- **Recency**: Calculated using exponential decay $e^{-0.3 \cdot t}$ where $t$ is age in years.
- **Author Credibility**: Verified against `trusted_orgs.json`. Supports **multi-author averaging** where individual scores are calculated and the mean is returned.
- **Citation Count**: Since no live citation database is integrated, we use a structural proxy (chunk depth). A keyword-stuffing penalty (50% reduction) is applied if the tag-to-word ratio exceeds 0.03.
- **Medical Safety**: A boolean keyword scan for phrases like "Not medical advice". PubMed is automatically granted 1.0 due to its peer-reviewed nature.

---

## Section 4: Edge Cases & Abuse Prevention

### 4.1 Edge Case Handling
- **Missing Date**: Assigned a neutral-stale score of **0.4** to prevent unknown dates from appearing "fresh". 
- **Missing Author**: Scored at **0.3** (penalty) UNLESS on a high-trust domain (e.g., Mayo Clinic), in which case the domain carries the weight (**0.65**).
- **Multiple Authors**: The engine identifies individual authors and applies the **averaging logic** required by the specification.
- **Missing Transcript**: Gracefully handles YouTube videos with no captions; `content_chunks` returns empty but metadata extraction continues.

### 4.2 Abuse Prevention
- **Fake Author Guard**: Cross-references every author string against a known organization whitelist.
- **SEO Spam Guard**: Detects "keyword stuffing" by analyzing tag density; penalized by 50% on the citation factor.
- **Outdated Content Guard**: Exponential decay ensures that even from a high-trust source, 10-year-old content cannot achieve a high score.
- **Medical Misinformation**: Penalizes blogs/videos that offer health advice without a standard medical disclaimer.
