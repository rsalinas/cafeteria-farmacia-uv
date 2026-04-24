#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from farmacafe_parser import ParseError, parse_menu_html

DEFAULT_URL = "https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu"
DEFAULT_REPORT_FILE = Path("parser_repair_context.json")
DEFAULT_PARSER_FILE = Path("farmacafe_parser.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build parser repair context for on-demand AI analysis")
    parser.add_argument("--url", default=DEFAULT_URL, help="Menu URL used to fetch html")
    parser.add_argument("--html-file", type=Path, help="Use local html file instead of downloading")
    parser.add_argument("--parser-file", type=Path, default=DEFAULT_PARSER_FILE, help="Parser source file")
    parser.add_argument("--report-file", type=Path, default=DEFAULT_REPORT_FILE, help="Output JSON report")
    return parser.parse_args()


def load_html(url: str, html_file: Path | None) -> tuple[str, str]:
    if html_file:
        return html_file.read_text(encoding="utf-8"), f"file:{html_file}"

    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    response.raise_for_status()
    return response.text, url


def main() -> int:
    args = parse_args()
    checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    try:
        html, source = load_html(args.url, args.html_file)
    except Exception as exc:
        print(f"Could not load HTML: {exc}")
        return 1

    try:
        parsed = parse_menu_html(html, source_url=source)
        parse_error = None
    except ParseError as exc:
        parsed = None
        parse_error = str(exc)

    try:
        parser_source = args.parser_file.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Could not read parser source: {exc}")
        return 1

    report = {
        "checked_at_utc": checked_at,
        "html_source": source,
        "parser_file": str(args.parser_file),
        "parse_error": parse_error,
        "parse_output": parsed,
        "parser_source": parser_source,
        "html_content": html,
        "instructions_for_ai": [
            "If parse_error is not null, update parser_source to support current html_content.",
            "Keep the parser small and deterministic.",
            "Preserve output schema used by parse_output.",
        ],
    }

    args.report_file.parent.mkdir(parents=True, exist_ok=True)
    args.report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Repair context written to {args.report_file}")
    if parse_error:
        print("Parser currently fails. You can now send this JSON to OpenAI API on demand.")
        return 2

    print("Parser currently works with the provided HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
