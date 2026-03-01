"""X/Twitter source (experimental).

Uses snscrape to search for AI research tweets without an API key.
This is fragile and may break when X changes their anti-scraping measures.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from knowledge_producer import Paper

SEARCH_QUERIES = [
    "#AIResearch",
    "#MachineLearning LLM paper",
    "#NeurIPS OR #ICML OR #ICLR paper",
    "new AI paper arxiv",
]


def fetch(days: int = 1, max_results: int = 100, ref_date: date | None = None) -> list[Paper]:
    """Fetch recent AI research tweets from X/Twitter using snscrape.

    This is experimental — snscrape may not be installed or may be broken.
    Failures are caught gracefully by the source registry.
    """
    try:
        import snscrape.modules.twitter as sntwitter
    except ImportError:
        print("    [twitter] snscrape not installed. Install with: pip install snscrape")
        return []
    except Exception:
        print("    [twitter] snscrape failed to load (may be broken with current X changes)")
        return []

    today = ref_date or datetime.now(timezone.utc).date()
    cutoff_date = today - timedelta(days=days)
    since_str = cutoff_date.strftime("%Y-%m-%d")

    papers: list[Paper] = []
    seen_urls: set[str] = set()

    for query in SEARCH_QUERIES:
        full_query = f"{query} since:{since_str}"
        try:
            scraper = sntwitter.TwitterSearchScraper(full_query)
            for i, tweet in enumerate(scraper.get_items()):
                if i >= max_results // len(SEARCH_QUERIES):
                    break

                tweet_url = tweet.url
                if tweet_url in seen_urls:
                    continue
                seen_urls.add(tweet_url)

                papers.append(
                    Paper(
                        title=tweet.rawContent[:120].split("\n")[0],
                        abstract=tweet.rawContent,
                        authors=[tweet.user.username],
                        url=tweet_url,
                        source="twitter",
                        published=tweet.date.replace(tzinfo=timezone.utc)
                        if tweet.date.tzinfo is None
                        else tweet.date,
                    )
                )
        except Exception as e:
            print(f"    [twitter] Query '{query}' failed: {e}")
            continue

    return papers
