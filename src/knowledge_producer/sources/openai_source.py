from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from knowledge_producer import Paper
from knowledge_producer.time_utils import now_pacific, today_pacific, to_pacific

OPENAI_RESEARCH_URL = "https://openai.com/research/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def fetch(days: int = 1, max_results: int = 500, ref_date: date | None = None) -> list[Paper]:
    """Fetch recent research posts from OpenAI."""
    today = ref_date or today_pacific()
    cutoff_date = today - timedelta(days=days)

    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(OPENAI_RESEARCH_URL, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    papers: list[Paper] = []

    # OpenAI lists research in card-based layouts
    for card in soup.select("a[href*='/research/'], a[href*='/index/']"):
        title_el = card.select_one("h3") or card.select_one("h2") or card.select_one("[class*='heading']")
        title = title_el.get_text(strip=True) if title_el else ""

        if not title or len(title) < 5:
            continue

        href = card.get("href", "")
        if href.startswith("/"):
            link = f"https://openai.com{href}"
        else:
            link = href

        desc_el = card.select_one("p") or card.select_one("[class*='desc']")
        abstract = desc_el.get_text(strip=True) if desc_el else ""

        date_el = card.select_one("time") or card.select_one("[class*='date']")
        published = _parse_date_text(date_el.get_text(strip=True)) if date_el else now_pacific()

        if to_pacific(published).date() < cutoff_date:
            continue

        papers.append(
            Paper(
                title=title,
                abstract=abstract,
                authors=["OpenAI"],
                url=link,
                source="openai",
                published=published,
            )
        )

        if len(papers) >= max_results:
            break

    return papers


def _parse_date_text(text: str) -> datetime:
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return now_pacific()
