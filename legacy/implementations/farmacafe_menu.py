#!/usr/bin/env python3

import argparse
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

DEFAULT_URL = (
    "https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu"
)


def _section_key(section_title):
    text = section_title.strip().lower()
    if "primer" in text or "primero" in text:
        return "primers"
    if "segon" in text or "segundo" in text:
        return "segons"
    if "postre" in text:
        return "postres"
    slug = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return slug or "altres"


def _element_classes(element):
    classes = element.get("class")
    if isinstance(classes, list):
        return classes
    if isinstance(classes, str):
        return [classes]
    return []


def _extract_clean_date(text):
    match = re.search(r"(\d{1,2}[\/-]\d{1,2}[\/-]\d{4})", text)
    if match:
        return match.group(1)
    return text.strip()


def generate_menu_data(url=DEFAULT_URL):
    data = {
        "url": url,
        "data_menu": "Sense data",
        "primers": [],
        "segons": [],
        "preu": None,
        "altres_seccions": {},
        "error": None,
    }

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        menu_div = soup.find("div", class_="menu")
        if not menu_div:
            data["error"] = "No s'ha trobat el contingut del menú."
            return data

        date_tag = menu_div.find("h6")
        if date_tag:
            data["data_menu"] = _extract_clean_date(date_tag.get_text(strip=True))

        for section in menu_div.find_all("h4"):
            section_name = section.get_text(strip=True)
            section_key = _section_key(section_name)
            dishes = []

            element = section.find_next_sibling()
            while (
                element and element.name != "h4" and "precio_menu" not in _element_classes(element)
            ):
                if element.name == "p" and "plato" in _element_classes(element):
                    dish_b = element.find("b")
                    dish_name = (
                        dish_b.get_text(strip=True) if dish_b else element.get_text(strip=True)
                    )
                    if dish_name:
                        dishes.append(dish_name)
                element = element.find_next_sibling()

            if section_key in ("primers", "segons"):
                data[section_key].extend(dishes)
            elif dishes:
                data["altres_seccions"][section_name] = dishes

        price = menu_div.find("p", class_="precio_menu")
        if price:
            data["preu"] = price.get_text(strip=True)

    except requests.RequestException as exc:
        data["error"] = f"Error HTTP en l'extracció: {exc}"
    except Exception as exc:
        data["error"] = f"Error en l'extracció: {exc}"

    return data


def render_menu_text(data):
    if data.get("error"):
        return data["error"]

    lines = [f"=== {data['data_menu']} ==="]

    if data["primers"]:
        lines.append("\nPrimers plats:")
        for dish in data["primers"]:
            lines.append(f"  - {dish}")

    if data["segons"]:
        lines.append("\nSegons plats:")
        for dish in data["segons"]:
            lines.append(f"  - {dish}")

    for section_name, dishes in data["altres_seccions"].items():
        lines.append(f"\n{section_name}:")
        for dish in dishes:
            lines.append(f"  - {dish}")

    if data["preu"]:
        lines.append(f"\nPREU: {data['preu']}")

    lines.append(f"\nMés informació: {data['url']}")
    return "\n".join(lines)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Scraper bàsic del menú de la cafeteria de Farmàcia UV"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Mostra l'eixida en JSON"
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="URL del menú a extraure")
    return parser


def main():
    args = build_parser().parse_args()
    data = generate_menu_data(url=args.url)

    if args.json_output:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_menu_text(data))

    return 1 if data.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
