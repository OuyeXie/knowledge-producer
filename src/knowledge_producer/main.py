from __future__ import annotations

import argparse
import io
import os
import sys
from datetime import date, datetime, timezone

from knowledge_producer.categorizer import categorize_papers
from knowledge_producer.dedup import dedup_papers, load_seen_papers
from knowledge_producer.focus import DEFAULT_FOCUS_TOPICS, match_focus
from knowledge_producer.llm_summarizer import enrich_focus_papers
from knowledge_producer.reporter import generate_report, save_report
from knowledge_producer.sources import available_sources, fetch_all_sources

_DEFAULT_FOCUS_STR = ",".join(DEFAULT_FOCUS_TOPICS)


class _TeeWriter(io.TextIOBase):
    """Write to both the original stream and a log file."""

    def __init__(self, original: io.TextIOBase, log_file: io.TextIOBase):
        self._original = original
        self._log_file = log_file

    def write(self, s: str) -> int:
        self._original.write(s)
        self._log_file.write(s)
        return len(s)

    def flush(self) -> None:
        self._original.flush()
        self._log_file.flush()


def _setup_logging(report_date: str, days: int, log_dir: str = "logs") -> io.TextIOBase | None:
    """Set up tee logging to a file. Returns the log file handle (to close later)."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
    filename = f"{report_date}-{days}d-{timestamp}.log"
    filepath = os.path.join(log_dir, filename)
    log_file = open(filepath, "w", encoding="utf-8")
    sys.stdout = _TeeWriter(sys.__stdout__, log_file)
    sys.stderr = _TeeWriter(sys.__stderr__, log_file)
    return log_file


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    all_sources = available_sources()
    parser = argparse.ArgumentParser(
        prog="knowledge-producer",
        description="Fetch recent AI research from multiple sources and generate a categorized report.",
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
        help="Maximum papers per source (default: 500)",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default=None,
        help=f"Comma-separated list of sources (default: all). Available: {', '.join(all_sources)}",
    )
    parser.add_argument(
        "--focus",
        type=str,
        default=_DEFAULT_FOCUS_STR,
        help=f"Comma-separated focus topics shown at the top of the report (default: {_DEFAULT_FOCUS_STR})",
    )
    parser.add_argument(
        "--no-focus",
        action="store_true",
        help="Disable the focus section entirely",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM summarization for focus papers (keyword matching only)",
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        choices=["openai", "anthropic"],
        default=None,
        help="LLM provider for focus summaries (default: auto-detect from API keys)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Reference date in YYYY-MM-DD format (default: today UTC). "
             "e.g. --date 2026-02-28 --days 1 fetches papers from Feb 27-28.",
    )
    parser.add_argument(
        "--dedup",
        type=str,
        nargs="?",
        const="all",
        default=None,
        help="Deduplicate against previous reports. "
             "Use --dedup (or --dedup all) to scan all reports in output dir, "
             "or --dedup file1.md,file2.md for specific files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    sources = args.sources.split(",") if args.sources else None
    source_label = ", ".join(sources) if sources else "all"

    ref_date: date | None = None
    if args.date:
        try:
            ref_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"Error: invalid date format '{args.date}', expected YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    # Set up log file
    report_date_str = (ref_date or datetime.now(timezone.utc).date()).isoformat()
    log_file = _setup_logging(report_date_str, args.days)

    focus_topics: list[str] = []
    if not args.no_focus:
        focus_topics = [t.strip() for t in args.focus.split(",") if t.strip()]

    date_label = ref_date.isoformat() if ref_date else "today"
    print(f"Fetching AI research from the last {args.days} day(s) from {date_label} [{source_label}]...")

    try:
        papers = fetch_all_sources(
            days=args.days,
            max_results=args.max_results,
            sources=sources,
            ref_date=ref_date,
        )
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)

    print(f"\nTotal: {len(papers)} unique items across sources.")

    # Dedup against previous reports
    if args.dedup:
        if args.dedup == "all":
            report_files = None  # scan all in output dir
        else:
            report_files = [f.strip() for f in args.dedup.split(",")]
        seen = load_seen_papers(report_dir=args.output, report_files=report_files)
        papers, num_removed = dedup_papers(papers, seen)
        print(f"Dedup: removed {num_removed} papers seen in previous reports, {len(papers)} remaining.")

    print("Categorizing...")

    categorize_papers(papers)

    # Build focus matches: {topic: [papers]}
    focus_matches: dict[str, list] = {}
    enriched_focus: dict[str, list] = {}
    llm_used = "disabled" if args.no_llm else "none"
    if focus_topics:
        focus_matches = match_focus(papers, focus_topics)
        focus_total = sum(len(v) for v in focus_matches.values())
        print(f"Focus: {focus_total} items matched across {len(focus_topics)} topic(s).")

        # LLM enrichment (if enabled and API key is set)
        if not args.no_llm:
            enriched_focus, llm_used = enrich_focus_papers(focus_matches, provider=args.llm_provider)

    tagged = sum(1 for p in papers if p.tags)
    print(f"Categorized {tagged} items ({len(papers) - tagged} uncategorized).")

    report_date = (ref_date or datetime.now(timezone.utc).date()).isoformat()

    # Build generation metadata for the report header
    gen_info = {
        "days": args.days,
        "date": report_date,
        "sources": source_label,
        "max_results": args.max_results,
        "dedup": args.dedup or "off",
        "focus": ", ".join(focus_topics) if focus_topics else "disabled",
        "llm": llm_used or "none",
    }

    content = generate_report(
        papers, report_date,
        focus_matches=focus_matches,
        enriched_focus=enriched_focus,
        generation_info=gen_info,
    )

    try:
        filepath = save_report(content, args.output, report_date=report_date, days=args.days)
    except OSError as e:
        print(f"Error writing report: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Report saved to {filepath}")

    # Close log
    if log_file:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        log_file.close()


if __name__ == "__main__":
    main()
