# 🧠 Scraper Engine: The "Explain Everything" Prompt

This prompt summarizes every technology, architectural decision, and library used in the **Scraper Engine** project. Use this for your own reference or to explain the project to others.

---

### 🧱 Architectural Concept: "The Modular Pipeline"
The project follows a **Dispatcher-Parser-Storage** architecture. 
1. **Dispatcher (`pipeline.py`)**: A central traffic controller that identifies the source type (Blog, YouTube, or PubMed) and routes the request to the correct specialized parser.
2. **Parsers (`scraper/`)**: Isolated modules that contain source-specific logic. This keeps the code "decoupled"—you can add a new source (like Twitter or LinkedIn) simply by adding a new parser file.
3. **Common Utilities (`utils/`)**: Shared logic (cleaning, chunking, tagging) that all parsers call to ensure data consistency.
4. **Data Contract (`schema.py`)**: Uses Pydantic to define exactly what a "document" looks like. If a parser tries to return bad data, the system catches it immediately.
5. **Partitioned Storage (`storage.py`)**: Saves data into separate JSON files (`blogs.json`, etc.) to prevent a single massive file that slows down over time.

---

### 📦 Technology Stack & Library Breakdown

#### **1. Core Infrastructure**
- **Python 3.10+**: The language of choice for its massive ecosystem of scraping and NLP libraries.
- **Pydantic**: The "Strict Parent" of the project. It validates data types (ensuring a `trust_score` is a float between 0 and 1, or that a `published_date` is a valid ISO string).
- **Pathlib**: Used for modern, cross-platform file path management (works on Windows, Mac, and Linux without change).

#### **2. Web Scraping & Extraction**
- **Newspaper3k**: A specialized library for "News" extraction. It doesn't just get HTML; it uses heuristics to find the "Main Text," "Author," and "Top Image."
- **Readability-lxml**: Our "Plan B" for blogs. It uses the same algorithm as Firefox/Safari's "Reader View" to strip away ads, navbars, and sidebars.
- **yt-dlp**: The gold standard for YouTube. It extracts metadata (views, likes, channel, upload date) without needing a heavy API key.
- **youtube-transcript-api**: A clever library that fetches closed captions directly from YouTube's internal player data.
- **Biopython (Entrez)**: A professional bioinformatics library used to talk to the NCBI PubMed databases via the official E-utilities API.

#### **3. Natural Language Processing (NLP)**
- **RAKE (Rapid Automatic Keyword Extraction)**: A statistical algorithm that finds important phrases by analyzing word frequency and their co-occurrence with other words.
- **NLTK (Natural Language Toolkit)**: The backbone for RAKE. We use it for its list of "Stopwords" (common words like 'the', 'is', 'at') to filter out noise.
- **Langdetect**: Uses profile-matching to detect 55 different languages based on character frequency.

#### **4. Utilities & Helpers**
- **Logging**: Abandoning `print()` for a real logging framework that saves traces to `scraper.log`.
- **Tqdm**: Provides the "spider" progress bar in the terminal so you know exactly how much work is left.
- **Requests**: The standard for sending HTTP requests, used with **User-Agent Rotation** to mimic different browsers and avoid getting blocked.

---

### 🛡️ Verification checklist (Self-Correction)
- [x] **Schema Validation**: Every JSON output matches the `ScrapedDocument` model? **Yes.**
- [x] **Deduplication**: Does it skip already-scraped URLs? **Yes, in `storage.py`.**
- [x] **Boilerplate Removal**: Are ads and nav links removed? **Yes, via Newspaper3k/Readability.**
- [x] **Cross-Ecosystem**: Does it handle Blogs, Video, and Science? **Yes, via 3 distinct scrapers.**
- [x] **Error Handling**: If a YouTube video is private, does the whole script crash? **No, it logs a failure and moves to the next source.**
