#!/usr/bin/env python3
"""Minimal parser for QRCarta menu HTML."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

PARSER_VERSION = "1.0.0"


class ParseError(Exception):
    """Raised when the expected HTML structure is not found."""


def _classes(element: Any) -> list[str]:
    classes = element.get("class")
    if isinstance(classes, list):
        return [str(c) for c in classes]
    if isinstance(classes, str):
        return [classes]
    return []


def _extract_date(text: str) -> str | None:
    match = re.search(r"(\d{1,2}[\/-]\d{1,2}[\/-]\d{4})", text)
    if match:
        return match.group(1)
    clean = text.strip()
    return clean or None


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return value or "section"


def parse_menu_html(html: str, source_url: str | None = None) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    menu_div = soup.find("div", class_="menu")
    if not menu_div:
        raise ParseError("menu div not found")

    restaurant = {
        "name": None,
        "address": None,
        "phone": None,
    }

    h1 = soup.find("h1")
    if h1:
        restaurant["name"] = h1.get_text(strip=True) or None

    copyright_div = soup.find("div", class_="copyright")
    if copyright_div:
        copyright_text = copyright_div.get_text(" ", strip=True)
        address_match = re.search(r"([^,]+,\s*\d+\s*-\s*[^<]+)", copyright_text)
        phone_match = re.search(r"(\d{3}\s*\d{2}\s*\d{2}\s*\d{2})", copyright_text)
        if address_match:
            restaurant["address"] = address_match.group(1).strip()
        if phone_match:
            restaurant["phone"] = phone_match.group(1).strip()

    date_tag = menu_div.find("h6")
    display_date = _extract_date(date_tag.get_text(" ", strip=True)) if date_tag else None

    sections = []
    for heading in menu_div.find_all("h4"):
        section_title = heading.get_text(" ", strip=True)
        dishes = []

        cursor = heading.find_next_sibling()
        while cursor and cursor.name != "h4" and "precio_menu" not in _classes(cursor):
            if cursor.name == "p" and "plato" in _classes(cursor):
                name_bold = cursor.find("b")
                dish_name = (name_bold.get_text(" ", strip=True) if name_bold else cursor.get_text(" ", strip=True)).strip()
                allergens = []
                allergen_titles = []

                allergen_row = cursor.find_next_sibling("p")
                if allergen_row and allergen_row.find_all("img"):
                    for img in allergen_row.find_all("img"):
                        item = {
                            "title": (img.get("title") or "").strip() or None,
                            "alt": (img.get("alt") or "").strip() or None,
                            "src": (img.get("src") or "").strip() or None,
                        }
                        allergens.append(item)
                        if item["title"]:
                            allergen_titles.append(item["title"])

                dishes.append(
                    {
                        "name": dish_name,
                        "allergens": allergens,
                        "allergen_titles": allergen_titles,
                        "raw_html": str(cursor),
                    }
                )

            cursor = cursor.find_next_sibling()

        if dishes:
            sections.append(
                {
                    "title": section_title,
                    "key": _slug(section_title),
                    "dishes": dishes,
                    "raw_html": str(heading),
                }
            )

    price_tag = menu_div.find("p", class_="precio_menu")
    price = price_tag.get_text(" ", strip=True) if price_tag else None

    includes = None
    for paragraph in menu_div.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        lower = text.lower()
        if "postre" in lower or "pan" in lower or "bebida" in lower:
            includes = text
            break

    legend_items = []
    legend_div = menu_div.find("div", class_="leyenda")
    if legend_div:
        for span in legend_div.find_all("span"):
            text = span.get_text(" ", strip=True)
            img = span.find("img")
            legend_items.append(
                {
                    "text": text or None,
                    "icon_alt": (img.get("alt") or "").strip() if img else None,
                    "icon_src": (img.get("src") or "").strip() if img else None,
                }
            )

    return {
        "parser_version": PARSER_VERSION,
        "source_url": source_url,
        "restaurant": restaurant,
        "menu": {
            "display_date": display_date,
            "sections": sections,
            "price": price,
            "includes": includes,
            "allergen_legend": legend_items,
            "raw_text": menu_div.get_text("\n", strip=True),
        },
        "meta": {
            "section_count": len(sections),
            "dish_count": sum(len(s["dishes"]) for s in sections),
        },
    }
