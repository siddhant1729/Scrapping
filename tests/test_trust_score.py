"""Tests for the trust score algorithm edge cases."""
import pytest
from scoring.trust_score import TrustScoreEngine

engine = TrustScoreEngine()


def _score(author="John Doe", published_date="2024-01-01",
           chunks=None, tags=None, url="https://example.com", source_type="blog"):
    """Helper that calls engine.compute() with sensible defaults."""
    return engine.compute(
        source_url=url,
        source_type=source_type,
        author=author,
        published_date=published_date,
        content_chunks=chunks or ["Content chunk one.", "Content chunk two."],
        topic_tags=tags or ["ai", "data"],
        raw_text="Some body text.",
    )


def test_score_range():
    score = _score()
    assert 0.0 <= score <= 1.0


def test_missing_author_does_not_crash():
    score = _score(author=None)
    assert isinstance(score, float)


def test_missing_date_does_not_crash():
    score = _score(published_date="")
    assert isinstance(score, float)


def test_outdated_content_penalised():
    recent = _score(published_date="2024-06-01")
    old = _score(published_date="2010-01-01")
    assert recent > old


def test_pubmed_scores_higher_than_unknown_blog():
    pubmed = _score(
        url="https://pubmed.ncbi.nlm.nih.gov/39848003/",
        source_type="pubmed",
        author="Smith J, Doe A",
        published_date="2023-09-01",
    )
    unknown = _score(
        url="https://some-random-blog.xyz/post",
        source_type="blog",
        author="Unknown",
        published_date="2015-01-01",
    )
    assert pubmed > unknown


def test_multiple_authors_averaged():
    """Engine must not crash on comma-separated author strings."""
    score = _score(author="Alice Smith, Bob Jones, Carol White")
    assert 0.0 <= score <= 1.0
