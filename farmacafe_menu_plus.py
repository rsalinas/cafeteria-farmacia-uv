#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from farmacafe_parser import ParseError, parse_menu_html

DEFAULT_URL = "https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu"
DEFAULT_STATE_FILE = Path(".state/farmacafe_menu_plus_state.json")


@dataclass
class FetchResult:
    html: str
    status_code: int
    fetched_at_utc: str


def fetch_html(url: str, timeout: int = 20) -> FetchResult:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return FetchResult(html=response.text, status_code=response.status_code, fetched_at_utc=fetched_at)


def build_normalized_snapshot(parsed: dict[str, Any]) -> dict[str, Any]:
    # display_date changes every day and is ignored for change detection.
    normalized = {
        "restaurant": parsed.get("restaurant"),
        "sections": [],
        "price": parsed.get("menu", {}).get("price"),
        "includes": parsed.get("menu", {}).get("includes"),
        "allergen_legend": parsed.get("menu", {}).get("allergen_legend"),
    }

    for section in parsed.get("menu", {}).get("sections", []):
        normalized["sections"].append(
            {
                "title": section.get("title"),
                "key": section.get("key"),
                "dishes": [
                    {
                        "name": dish.get("name"),
                        "allergen_titles": dish.get("allergen_titles", []),
                    }
                    for dish in section.get("dishes", [])
                ],
            }
        )

    return normalized


def snapshot_fingerprint(snapshot: dict[str, Any]) -> str:
    blob = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def read_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def build_output(url: str, fetch_result: FetchResult, parsed: dict[str, Any], normalized: dict[str, Any], changed: bool, previous: dict[str, Any] | None, state_file: Path, include_html: bool) -> dict[str, Any]:
    current_fp = snapshot_fingerprint(normalized)
    previous_fp = (previous or {}).get("fingerprint")

    output = {
        "error": None,
        "source": {
            "url": url,
            "http_status": fetch_result.status_code,
            "fetched_at_utc": fetch_result.fetched_at_utc,
            "html_sha256": hashlib.sha256(fetch_result.html.encode("utf-8")).hexdigest(),
        },
        "parsed": parsed,
        "normalized_snapshot": normalized,
        "change_detection": {
            "state_file": str(state_file),
            "has_previous_snapshot": previous is not None,
            "previous_checked_at_utc": (previous or {}).get("checked_at_utc"),
            "current_checked_at_utc": fetch_result.fetched_at_utc,
            "previous_fingerprint": previous_fp,
            "current_fingerprint": current_fp,
            "changed_since_previous_snapshot": changed,
            "comparison_basis": "normalized snapshot without display_date",
        },
    }

    if include_html:
        output["source"]["html"] = fetch_result.html

    return output


def render_text(data: dict[str, Any]) -> str:
    if data.get("error"):
        return f"ERROR: {data['error']}"

    parsed = data["parsed"]
    menu = parsed["menu"]
    lines = []

    lines.append(f"Menu date shown by site: {menu.get('display_date') or 'unknown'}")
    lines.append(f"Checked at UTC: {data['source']['fetched_at_utc']}")
    lines.append(f"Changed vs previous snapshot: {data['change_detection']['changed_since_previous_snapshot']}")

    restaurant = parsed.get("restaurant", {})
    if restaurant.get("name"):
        lines.append(f"Restaurant: {restaurant['name']}")
    if restaurant.get("address"):
        lines.append(f"Address: {restaurant['address']}")
    if restaurant.get("phone"):
        lines.append(f"Phone: {restaurant['phone']}")

    for section in menu.get("sections", []):
        lines.append(f"\n{section['title']}:")
        for dish in section.get("dishes", []):
            allergens = ", ".join(dish.get("allergen_titles", []))
            suffix = f" [{allergens}]" if allergens else ""
            lines.append(f"  - {dish.get('name')}{suffix}")

    if menu.get("price"):
        lines.append(f"\nPrice: {menu['price']}")
    if menu.get("includes"):
        lines.append(f"Includes: {menu['includes']}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extended menu scraper with change detection")
    parser.add_argument("--url", default=DEFAULT_URL, help="Menu URL")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print JSON output")
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE, help="Path to state snapshot file")
    parser.add_argument("--include-html", action="store_true", help="Include raw HTML in JSON output")
    parser.add_argument("--no-state-update", action="store_true", help="Compute changes but do not write state file")
    parser.add_argument("--exit-code-on-change", type=int, default=None, help="Optional exit code when a change is detected")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        fetch_result = fetch_html(args.url)
    except requests.RequestException as exc:
        payload = {"error": f"HTTP fetch error: {exc}"}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json_output else payload["error"])
        return 1

    try:
        parsed = parse_menu_html(fetch_result.html, source_url=args.url)
    except ParseError as exc:
        payload = {
            "error": f"parse error: {exc}",
            "source": {
                "url": args.url,
                "fetched_at_utc": fetch_result.fetched_at_utc,
                "http_status": fetch_result.status_code,
            },
        }
        if args.json_output:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload["error"])
        return 2

    normalized = build_normalized_snapshot(parsed)
    previous = read_state(args.state_file)
    current_fp = snapshot_fingerprint(normalized)
    previous_fp = (previous or {}).get("fingerprint")
    changed = previous_fp is not None and previous_fp != current_fp

    output = build_output(
        url=args.url,
        fetch_result=fetch_result,
        parsed=parsed,
        normalized=normalized,
        changed=changed,
        previous=previous,
        state_file=args.state_file,
        include_html=args.include_html,
    )

    if not args.no_state_update:
        write_state(
            args.state_file,
            {
                "checked_at_utc": fetch_result.fetched_at_utc,
                "fingerprint": current_fp,
                "normalized_snapshot": normalized,
            },
        )

    if args.json_output:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(render_text(output))

    if output.get("error"):
        return 1

    if changed and args.exit_code_on_change is not None:
        return args.exit_code_on_change

    return 0


if __name__ == "__main__":
    sys.exit(main())
