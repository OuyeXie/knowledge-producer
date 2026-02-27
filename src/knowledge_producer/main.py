from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from knowledge_producer.categorizer import categorize_papers
from knowledge_producer.fetcher import fetch_papers
from knowledge_producer.reporter import generate_report, save_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="knowledge-producer",
        description="Fetch recent AI research papers from arXiv and generate a categorized report.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days to look back (default: 1)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports",
        help="Output directory for reports (default: reports)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=500,
        help="Maximum number of papers to fetch (default: 500)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    print(f"Fetching AI research papers from the last {args.days} day(s)...")

    try:
        papers = fetch_papers(days=args.days, max_results=args.max_results)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching papers: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(papers)} papers. Categorizing...")

    categorize_papers(papers)

    tagged = sum(1 for p in papers if p.tags)
    print(f"Categorized {tagged} papers ({len(papers) - tagged} uncategorized).")

    report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = generate_report(papers, report_date)

    try:
        filepath = save_report(content, args.output)
    except OSError as e:
        print(f"Error writing report: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Report saved to {filepath}")


if __name__ == "__main__":
    main()
