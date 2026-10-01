# Sorties à Paris

Agenda hebdomadaire des sorties culturelles à Paris (cinéma, expositions, théâtre, spectacles, conférences), tenu à jour par un agent IA.

- **Site** : statique (`index.html`, `style.css`, `app.js`), servi par GitHub Pages depuis la branche `main`.
- **Données** : `data/events.json`, réécrit chaque semaine.
- **Agent** : une routine Claude Code dans le cloud qui tourne chaque lundi à 8h (heure de Paris) et suit les instructions de [`AGENT.md`](AGENT.md).

## Fonctionnement de l'agent

1. Chaque lundi à 5h UTC, une GitHub Action lance `scripts/fetch_opendata.py`, qui récupère les candidats de l'API open data [« Que faire à Paris »](https://opendata.paris.fr/explore/dataset/que-faire-a-paris-/).
2. L'agent complète par recherche web (films à l'affiche, grandes expositions, théâtres et salles majeurs).
3. Il retient environ 120 événements, écrit `data/events.json` et lance `scripts/validate.py`.
4. Il commit et push : GitHub Pages republie le site.

## En local

```bash
python3 scripts/fetch_opendata.py          # candidats dans data/opendata-candidates.json
python3 scripts/validate.py                # vérifie et nettoie data/events.json
python3 -m http.server 8742                # puis http://localhost:8742
```

Pour modifier la sélection (sources, quotas par catégorie, critères), il suffit d'éditer `AGENT.md` : la routine le relit à chaque passage.
