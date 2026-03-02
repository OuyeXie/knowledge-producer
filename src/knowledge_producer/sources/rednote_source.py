"""RedNote/Xiaohongshu source (experimental).

Attempts to scrape AI research content from Xiaohongshu.
This is highly experimental — Xiaohongshu has aggressive anti-scraping
measures and may require Chinese phone authentication.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from knowledge_producer import Paper
from knowledge_producer.time_utils import now_pacific, today_pacific

REDNOTE_SEARCH_URL = "https://www.xiaohongshu.com/search_result"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

SEARCH_TERMS = ["AI论文", "大模型", "人工智能研究", "LLM", "机器学习", "每日论文"]


def fetch(days: int = 1, max_results: int = 100, ref_date: date | None = None) -> list[Paper]:
    """Attempt to fetch AI research posts from RedNote/Xiaohongshu.

    This is experimental and will likely fail without proper authentication.
    Failures are caught gracefully by the source registry.
    """
    today = ref_date or today_pacific()
    cutoff_date = today - timedelta(days=days)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    papers: list[Paper] = []
    seen_urls: set[str] = set()

    for term in SEARCH_TERMS:
        try:
            resp = requests.get(
                REDNOTE_SEARCH_URL,
                params={"keyword": term},
                headers=headers,
                timeout=15,
            )
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select("a[href*='/explore/'], a[href*='/discovery/']"):
                title_el = card.select_one("span") or card.select_one("p")
                title = title_el.get_text(strip=True) if title_el else ""

                if not title or len(title) < 3:
                    continue

                href = card.get("href", "")
                if href.startswith("/"):
                    link = f"https://www.xiaohongshu.com{href}"
                else:
                    link = href

                if link in seen_urls:
                    continue
                seen_urls.add(link)

                papers.append(
                    Paper(
                        title=title,
                        abstract="",
                        authors=[],
                        url=link,
                        source="rednote",
                        published=now_pacific(),
                    )
                )

                if len(papers) >= max_results:
                    return papers

        except requests.RequestException:
            continue

    return papers
