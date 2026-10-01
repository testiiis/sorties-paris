#!/usr/bin/env python3
"""Extrait les événements culturels de l'API open data « Que faire à Paris ».

Produit une liste de candidats déjà au format de data/events.json, que l'agent
trie et complète ensuite par recherche web.

Usage : python3 scripts/fetch_opendata.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]
        [--out .cache/opendata.json]
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/records"
PAGE = 100

# Ordre important : la première règle qui correspond l'emporte.
TAG_RULES = [
    ("conference", {"Conférence"}),
    ("exposition", {"Expo"}),
    ("theatre", {"Théâtre"}),
    ("spectacle", {"Danse", "Concert", "Spectacle musical", "Cirque", "Humour", "Opéra"}),
    ("cinema", {"Ecrans"}),
]
EXCLUDED_TAGS = {"Sport", "Atelier", "Solidarité", "Santé"}


def categorize(tags):
    tagset = set(tags)
    for category, wanted in TAG_RULES:
        if tagset & wanted:
            return category
    return None


def strip_html(text, limit=280):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def slugify(text):
    text = text.lower()
    for a, b in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"), ("ùûü", "u"), ("ç", "c")):
        text = re.sub(f"[{a}]", b, text)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:60]


def fetch(start, end):
    where = f'date_end >= "{start}" and date_start <= "{end}T23:59:59" and address_city like "Paris"'
    offset = 0
    while True:
        params = urllib.parse.urlencode({"where": where, "limit": PAGE, "offset": offset})
        with urllib.request.urlopen(f"{API}?{params}", timeout=60) as resp:
            batch = json.load(resp).get("results", [])
        yield from batch
        if len(batch) < PAGE or offset + PAGE >= 9900:
            return
        offset += PAGE


def to_event(rec):
    tags = [t for t in (rec.get("qfap_tags") or "").split(";") if t]
    if set(tags) & EXCLUDED_TAGS and not categorize(tags):
        return None
    category = categorize(tags)
    if not category:
        return None
    zipcode = (rec.get("address_zipcode") or "").strip()
    price_type = (rec.get("price_type") or "").lower()
    free = price_type == "gratuit"
    price = "Gratuit" if free else strip_html(rec.get("price_detail") or "Payant", 120)
    return {
        "id": slugify(f"{rec.get('title', '')}-{rec.get('id', '')}"),
        "category": category,
        "title": html.unescape(rec.get("title") or "").strip(),
        "description": strip_html(rec.get("lead_text") or rec.get("description")),
        "venue": (rec.get("address_name") or "").strip(),
        "address": " ".join(filter(None, [rec.get("address_street"), zipcode, "Paris"])),
        "arrondissement": zipcode if zipcode.startswith("75") else "",
        "start_date": (rec.get("date_start") or "")[:10],
        "end_date": (rec.get("date_end") or "")[:10],
        "schedule": strip_html((rec.get("date_description") or "").replace("<br />", " · "), 200),
        "price": price,
        "free": free,
        "url": rec.get("url") or rec.get("access_link") or "",
        "image": rec.get("cover_url") or "",
        "tags": [t for t in tags if t not in {"Expo", "Théâtre", "Conférence", "Ecrans"}],
        "source": "opendata.paris.fr",
    }


def main():
    today = dt.date.today()
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=today.isoformat())
    parser.add_argument("--end", default=(today + dt.timedelta(days=6)).isoformat())
    parser.add_argument("--out", default=".cache/opendata.json")
    args = parser.parse_args()

    events = [e for e in map(to_event, fetch(args.start, args.end)) if e and e["title"]]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=1)

    counts = {}
    for e in events:
        counts[e["category"]] = counts.get(e["category"], 0) + 1
    print(f"{len(events)} candidats écrits dans {args.out} : {counts}", file=sys.stderr)


if __name__ == "__main__":
    main()
