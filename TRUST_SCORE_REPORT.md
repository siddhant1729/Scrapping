# Trust Score System — Mathematical Report

## Section 1: Formula, Factor Weights & Justification

### 1.1 The Core Equation

The Trust Score (TS) is a **weighted linear combination** of five normalized sub-scores:

$$TS = \sum_{i=1}^{5} (w_i \cdot s_i)$$

Where:
- $w_i$ = the weight for factor $i$ (all weights sum to **1.0**)
- $s_i$ = the normalized score for factor $i$, in range $[0, 1]$

### 1.2 Factor Weights Table

| # | Factor | Weight ($w_i$) | Rationale |
|---|---|---|---|
| ① | Domain Authority | **0.30** | The publisher is the strongest proxy for credibility |
| ② | Recency | **0.25** | Stale information in tech/medicine carries real risk |
| ③ Content Quality | **0.20** | Empty documents are untrustworthy regardless of source |
| ④ | Author Trust | **0.15** | Named/recognized authors signal accountability |
| ⑤ | Medical Safety | **0.10** | Disclaimer presence is a regulatory and ethical marker |

### 1.3 Factor Logic & Normalization

#### ① Domain Authority ($s_{domain}$, $w=0.30$)
A tiered whitelist lookup against `scoring/trusted_orgs.json`:

| Tier | Score | Examples |
|---|---|---|
| **PubMed** (always) | 1.0 | pubmed.ncbi.nlm.nih.gov, ncbi.nlm.nih.gov |
| **High** | 1.0 | nature.com, bbc.com, nih.gov, who.int, reuters.com |
| **Medium** | 0.5 | medium.com, blog.google, openai.com, huggingface.co |
| **Unknown** | 0.15 | Any unverified or new domain |

Subdomain traversal is applied: `news.bbc.co.uk` resolves to the `bbc.co.uk` tier.

#### ② Recency ($s_{recency}$, $w=0.25$)
An **exponential decay function** penalizes older content:

$$s_{recency} = e^{-\lambda \cdot t}$$

Where $t$ = age in years, $\lambda = 0.3$ (decay constant).

| Age | Score |
|---|---|
| 0 years (today) | 1.00 |
| 1 year | 0.74 |
| 3 years | 0.41 |
| 5 years | 0.22 |
| 10 years | 0.05 |

**Missing date** → Stale penalty: $s = 0.4$ (not zero, because absence of date ≠ wrong content).

#### ③ Content Quality ($s_{quality}$, $w=0.20$)
Based on chunk count (proxy for substantive length):

| Chunks | Base Score |
|---|---|
| 0 | 0.10 |
| 1 | 0.40 |
| 2 | 0.65 |
| 3–4 | 0.85 |
| 5+ | 1.00 |

**SEO Spam Penalty**: If `len(topic_tags) / total_words > 0.03`, the base score is multiplied by **0.5**. This catches keyword-stuffed articles where tags are unnaturally dense.

#### ④ Author Trust ($s_{author}$, $w=0.15$)
A lookup against the `trusted_authors` and `trusted_orgs` lists in `trusted_orgs.json`:

| Condition | Score |
|---|---|
| Matched in trusted_orgs.json | 1.0 |
| Named (not matched) | 0.7 |
| Missing on a high-trust domain | 0.65 |
| Missing on an unknown domain | 0.3 |

The 0.65 "high-domain carry" handles the spec case: *"a Mayo Clinic article with no specific author — the domain score carries the weight."*

#### ⑤ Medical Safety ($s_{medical}$, $w=0.10$)
Boolean check for 9 disclaimer phrase patterns:

| Source Type | Logic | Score |
|---|---|---|
| PubMed | Always safe (peer-reviewed) | 1.0 |
| Blog / YouTube | Disclaimer phrase found | 1.0 |
| Blog / YouTube | No disclaimer found | 0.0 |

---

## Section 2: Edge Cases & "Friday Evening Slowness" Analysis

### 2.1 Missing Metadata Handling

| Missing Field | Strategy | Justification |
|---|---|---|
| No `published_date` | Recency score = **0.4** | Neutral-stale penalty; not 0 because absence ≠ false content |
| No `author` | Author score = **0.3** or **0.65** | Domain carries weight when publisher is known |
| Empty `content_chunks` | Quality score = **0.10** | Non-zero minimum — the URL itself is still a signal |
| Keyword Stuffing | Quality score × **0.5** | Tag ratio guard at `tags/words > 0.03` |

### 2.2 "Friday Evening Slowness" — Bottleneck Analysis

This scenario describes high-latency conditions where:
1. **NCBI's Entrez API** slows down under load (evenings, weekends)
2. **YouTube's transcript server** rate-limits aggressive scrapers
3. **News sites** (BBC, Nature) detect bot traffic and slow responses

**Root Cause**: All 6 sources are scraped **sequentially** in the current implementation. A single slow source blocks the entire pipeline.

**Mitigation Strategies Implemented:**
| Bottleneck | Mitigation |
|---|---|
| PubMed/NCBI rate limit | `REQUEST_INTERVAL = 0.4s` between requests; supports API key for 10 req/s |
| YouTube transcript | 2-second `sleep_sec` delay; v1.0+ instance API used to avoid deprecated endpoints |
| Blog anti-bot walls | User-Agent rotation from a pool of 5 real browser fingerprints |
| Full pipeline slowness | Error isolation — one failure doesn't block others; `tqdm` shows live progress |

**Future Optimization**: Rewrite the main loop using `asyncio` + `aiohttp` for parallel async scraping, reducing wall-clock time from ~36 seconds to ~8 seconds.
