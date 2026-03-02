from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from time import mktime

import feedparser

from knowledge_producer import Paper
from knowledge_producer.time_utils import today_pacific, to_pacific

FEED_URLS = [
    "https://medium.com/feed/tag/artificial-intelligence",
    "https://medium.com/feed/tag/machine-learning",
    "https://medium.com/feed/tag/deep-learning",
    "https://medium.com/feed/tag/llm",
]


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", clean).strip()


def _parse_date(entry: dict) -> datetime | None:
    """Extract published date from a feed entry."""
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
    return None


def fetch(days: int = 1, max_results: int = 500, ref_date: date | None = None) -> list[Paper]:
    """Fetch recent AI articles from Medium RSS feeds."""
    today = ref_date or today_pacific()
    cutoff_date = today - timedelta(days=days)

    papers: list[Paper] = []
    seen_urls: set[str] = set()

    for feed_url in FEED_URLS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            link = entry.get("link", "")
            if not link or link in seen_urls:
                continue
            seen_urls.add(link)

            published = _parse_date(entry)
            if not published or to_pacific(published).date() < cutoff_date:
                continue

            title = entry.get("title", "").strip()
            summary = _strip_html(entry.get("summary", entry.get("description", "")))
            author = entry.get("author", "")

            if not title:
                continue

            papers.append(
                Paper(
                    title=title,
                    abstract=summary[:1000] if summary else "",
                    authors=[author] if author else [],
                    url=link,
                    source="medium",
                    published=published,
                )
            )

            if len(papers) >= max_results:
                return papers

    return papers
