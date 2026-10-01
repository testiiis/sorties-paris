#!/usr/bin/env python3
"""Valide, nettoie et trie data/events.json.

- vérifie les champs obligatoires, catégories, dates et URL ;
- supprime les événements terminés avant le début de la semaine et les doublons ;
- trie par catégorie puis par date de fin, et réécrit le fichier.

Code de sortie 1 s'il reste des erreurs bloquantes (à corriger avant de commit).
Usage : python3 scripts/validate.py [chemin]
"""
import datetime as dt
import json
import re
import sys
import unicodedata

CATEGORIES = ["cinema", "exposition", "conference", "theatre", "spectacle"]
REQUIRED = ["id", "category", "title", "venue", "start_date", "end_date", "url"]
MIN_TOTAL = 60


def norm(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def parse_date(value):
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/events.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    errors, warnings = [], []
    week = data.get("week") or {}
    week_start, week_end = parse_date(week.get("start")), parse_date(week.get("end"))
    if not (week_start and week_end and week_start <= week_end):
        errors.append("week.start / week.end manquants ou invalides")
    if not data.get("generated_at"):
        errors.append("generated_at manquant")

    kept, seen_keys, seen_ids = [], set(), set()
    for i, ev in enumerate(data.get("events", [])):
        label = f"#{i} « {ev.get('title', '?')} »"
        missing = [k for k in REQUIRED if not ev.get(k)]
        if missing:
            errors.append(f"{label} : champs manquants {missing}")
            continue
        if ev["category"] not in CATEGORIES:
            errors.append(f"{label} : catégorie inconnue « {ev['category']} »")
            continue
        start, end = parse_date(ev["start_date"]), parse_date(ev["end_date"])
        if not (start and end) or end < start:
            errors.append(f"{label} : dates invalides {ev['start_date']} → {ev['end_date']}")
            continue
        if not re.match(r"^https?://", ev["url"]):
            errors.append(f"{label} : url invalide")
            continue
        if week_start and end < week_start:
            warnings.append(f"{label} : terminé avant la semaine, retiré")
            continue
        if week_end and start > week_end:
            warnings.append(f"{label} : commence après la semaine, retiré")
            continue
        key = (norm(ev["title"]), norm(ev["venue"]))
        if key in seen_keys:
            warnings.append(f"{label} : doublon, retiré")
            continue
        seen_keys.add(key)
        if ev["id"] in seen_ids:
            ev["id"] = f"{ev['id']}-{i}"
        seen_ids.add(ev["id"])
        ev.setdefault("free", False)
        ev.setdefault("tags", [])
        kept.append(ev)

    def sort_key(e):
        # Films : les plus récents d'abord. Autres : ceux qui se terminent le plus tôt d'abord.
        when = -parse_date(e["start_date"]).toordinal() if e["category"] == "cinema" else parse_date(e["end_date"]).toordinal()
        return (CATEGORIES.index(e["category"]), when, norm(e["title"]))

    kept.sort(key=sort_key)
    data["events"] = kept

    counts = {c: sum(e["category"] == c for e in kept) for c in CATEGORIES}
    for c, n in counts.items():
        if n == 0:
            errors.append(f"aucun événement dans la catégorie « {c} »")
    if len(kept) < MIN_TOTAL:
        errors.append(f"seulement {len(kept)} événements (minimum {MIN_TOTAL})")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")
    print(f"{len(kept)} événements : {counts}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
