"""
parsers/youtube_parser.py
--------------------------
Extracts YouTube video metadata and transcript using yt-dlp + youtube-transcript-api.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from schema import ScrapedDocument
from utils import chunk_transcript, detect_language, extract_topic_tags
from scoring.trust_score import TrustScoreEngine

_trust_engine = TrustScoreEngine()

logger = logging.getLogger(__name__)


def _extract_video_id(url: str) -> str:
    """Parse the video ID from a YouTube URL."""
    import re
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_\-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    # If URL is already a raw video ID
    if len(url) == 11 and url.replace("-", "").replace("_", "").isalnum():
        return url
    raise ValueError(f"Cannot extract video ID from: {url}")


def _fetch_metadata(video_id: str) -> dict:
    """
    Fetch video metadata using yt-dlp (no download).
    Returns dict with: title, channel, description, upload_date.
    """
    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }

    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    upload_date = info.get("upload_date", "")
    if upload_date and len(upload_date) == 8:
        # YYYYMMDD → YYYY-MM-DD
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

    return {
        "title": info.get("title", ""),
        "channel": info.get("channel") or info.get("uploader", "Unknown"),
        "description": info.get("description", ""),
        "upload_date": upload_date,
    }


def _fetch_transcript(video_id: str) -> Optional[list]:
    """
    Fetch transcript segments via youtube-transcript-api.
    Supports both v0.x (class-method API) and v1.0+ (instance API).
    Returns list of segment dicts, or None if not available.
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    # --- Try new v1.0+ instance-based API first ---
    try:
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id)
        # v1.0+ returns FetchedTranscript; convert to list of dicts
        if hasattr(fetched, "__iter__"):
            segments = [
                {"text": s.text if hasattr(s, "text") else s.get("text", ""),
                 "start": s.start if hasattr(s, "start") else s.get("start", 0)}
                for s in fetched
            ]
            if segments:
                return segments
    except Exception:
        pass  # fall through to legacy API

    # --- Fall back to legacy v0.x class-method API ---
    try:
        from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except Exception:
                transcript = next(iter(transcript_list))
        return transcript.fetch()
    except Exception as exc:
        logger.warning("Transcript fetch error for %s: %s", video_id, exc)
        return None


def parse_youtube(url: str, sleep_sec: float = 2.0) -> ScrapedDocument:
    """
    Extract metadata and transcript from a YouTube video URL.

    Parameters
    ----------
    url : str
        Full YouTube URL or video ID.
    sleep_sec : float
        Polite delay between API calls (seconds).
    """
    logger.info("YouTube parser → %s", url)
    time.sleep(sleep_sec)

    video_id = _extract_video_id(url)
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"

    # Metadata
    try:
        meta = _fetch_metadata(video_id)
    except Exception as exc:
        logger.error("yt-dlp metadata extraction failed for %s: %s", video_id, exc)
        meta = {"title": "", "channel": "Unknown", "description": "", "upload_date": ""}

    time.sleep(sleep_sec)

    # Transcript
    segments = _fetch_transcript(video_id)
    if segments is None:
        logger.warning("Video %s has no transcript — content_chunks will be empty.", video_id)
        content_chunks = []
    else:
        content_chunks = chunk_transcript(segments, max_words=200)

    # Use description + transcript for NLP
    full_text = meta.get("description", "") + " " + " ".join(content_chunks)
    language = detect_language(full_text)
    topic_tags = extract_topic_tags(full_text)

    author = meta.get("channel", "Unknown")
    published_date = meta.get("upload_date", "")

    trust_score = _trust_engine.compute(
        source_url=canonical_url,
        source_type="youtube",
        author=author,
        published_date=published_date,
        content_chunks=content_chunks,
        topic_tags=topic_tags,
        raw_text=full_text,
    )

    return ScrapedDocument(
        source_url=canonical_url,
        source_type="youtube",
        author=author,
        published_date=published_date,
        language=language,
        region=None,
        topic_tags=topic_tags,
        trust_score=trust_score,
        content_chunks=content_chunks,
    )
