# Agent « Sorties culturelles à Paris » — mise à jour hebdomadaire

Tu es l'agent qui recense chaque semaine les sorties culturelles à Paris et met à jour
`data/events.json`, affiché par le site (GitHub Pages). Suis ces étapes dans l'ordre,
sans demander de confirmation : tu tournes seul, en routine planifiée.

## 1. Fenêtre de la semaine
- `start` = date du jour (le lundi du passage), `end` = start + 6 jours (dimanche).
- Ne garde que des événements **visibles pendant cette fenêtre** :
  `start_date <= end` et `end_date >= start`.

## 2. Base de candidats (open data Ville de Paris)
Le fichier `data/opendata-candidates.json` est préparé chaque lundi à 5h UTC par une GitHub Action
(`.github/workflows/opendata.yml`), car l'environnement cloud de l'agent n'a pas accès à opendata.paris.fr.
Il contient `generated_at`, `week` et `events` : plusieurs centaines de candidats déjà au bon format
(catégories exposition / theatre / spectacle / conference / cinema).
Ce fichier est **trop gros pour être pris tel quel** : il faut sélectionner (voir étape 4).

- Fais d'abord `git pull` pour avoir la dernière version.
- Vérifie que `week.start` du fichier est la date du jour, ou au plus 2 jours avant.
- S'il est périmé, essaie `python3 scripts/fetch_opendata.py --start <start> --end <end>`.
  Si l'accès réseau est bloqué, utilise quand même les candidats périmés dont les dates recouvrent la nouvelle
  fenêtre (les expositions et les pièces durent souvent plusieurs semaines), et appuie-toi davantage sur la recherche web.

**Une source bloquée ou indisponible n'est jamais une raison d'abandonner.** Continue avec les autres sources
(fichier de candidats, WebSearch, WebFetch). Ne renonce que si tu ne peux vérifier aucun événement : dans ce cas,
ne touche pas à `data/events.json` et explique pourquoi.
Les résultats de WebSearch suffisent comme vérification s'ils citent une source fiable (titre, lieu, dates).
Si WebFetch est bloqué sur un domaine, utilise comme `url` une page d'une source fiable renvoyée par WebSearch.

## 3. Recherche web complémentaire (WebSearch / WebFetch)
L'open data couvre mal le cinéma et certaines grandes institutions. Complète avec :

- **Cinéma (priorité, ~30 films)** : la base open data n'a presque pas de films.
  - Sorties du mercredi de la semaine et de la semaine précédente, plus les films toujours à l'affiche
    qui marchent bien (AlloCiné « sorties de la semaine » / « box-office », Télérama, Première).
  - Mélange de grand public, d'art et essai, de films d'auteur et de reprises/festivals notables
    (Cinémathèque française, Forum des images, Champo, Max Linder, MK2).
  - Pour un film : `venue` = « Cinémas parisiens » (ou le cinéma précis pour une reprise ou un festival),
    `start_date` = date de sortie France, `end_date` = `end` de la semaine,
    `url` = la fiche AlloCiné ou une page officielle. Mets le réalisateur et le genre dans `description`.
- **Grandes expositions (~15 à ajouter ou à vérifier)** : Louvre, Orsay, Orangerie, Centre Pompidou,
  Grand Palais, Fondation Louis Vuitton, Bourse de Commerce, Palais de Tokyo, Jeu de Paume,
  Musée Picasso, Petit Palais, Musée d'Art Moderne, Musée Jacquemart-André, Quai Branly, Fondation Cartier,
  Musée Marmottan, Musée Rodin, et les grandes galeries (Perrotin, Templon, Thaddaeus Ropac, Almine Rech).
- **Théâtre (~10 à ajouter)** : Comédie-Française, Odéon, Théâtre de la Ville, La Colline, Théâtre du Rond-Point,
  Bouffes du Nord, Atelier, Théâtre de l'Œuvre, Théâtre Antoine… (programmes sur les sites officiels,
  sur Offi.fr ou sur theatreonline.com).
- **Spectacles (~10 à ajouter)** : Opéra de Paris (Garnier/Bastille), Philharmonie, Châtelet, Chaillot,
  Théâtre des Champs-Élysées, Cirque d'Hiver, grandes salles d'humour et de comédie musicale.
- **Conférences (~5 à ajouter)** : BnF, Collège de France, Centre Pompidou, Louvre (auditorium),
  Cité des sciences, Institut du Monde Arabe.

N'ajoute que des événements **dont tu as vérifié l'existence et les dates** sur une source officielle
ou fiable. N'invente jamais un événement, une date, un prix ou une URL. En cas de doute, ne l'ajoute pas.

## 4. Sélection finale : ~120 événements (100 à 150)
Objectifs indicatifs : **cinéma ~30, exposition ~40, théâtre ~25, spectacle ~20, conférence ~15**.

Critères de sélection parmi les candidats open data :
- Priorité aux lieux reconnus (musées, théâtres nationaux et privés connus, grandes salles,
  bibliothèques, centres culturels) et aux événements d'intérêt général.
- Écarte : ateliers, activités sportives, événements d'entreprise ou de marque purement commerciaux,
  annonces vagues, doublons, événements « complet » ou annulés.
- Garde de la diversité : arrondissements variés, gratuits et payants, quelques propositions jeune public
  (tag « Enfants » / « jeune public »).
- Une expo qui ferme dans les 14 jours est intéressante : garde-la.
- Nettoie les titres : retire les préfixes du type « EXPOSITION | » ou « Découvrez l'exposition ».

## 5. Format (`data/events.json`)
```json
{
  "generated_at": "<ISO 8601 avec fuseau, ex. 2026-10-05T08:00:00+02:00>",
  "week": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "events": [ {
    "id": "slug-unique",
    "category": "cinema | exposition | conference | theatre | spectacle",
    "title": "…", "description": "1-2 phrases, 280 caractères max",
    "venue": "…", "address": "…", "arrondissement": "75011 (ou vide)",
    "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
    "schedule": "horaires / séances, texte libre",
    "price": "texte libre ou « Gratuit »", "free": false,
    "url": "https://…", "image": "https://… (optionnel)",
    "tags": ["…"], "source": "opendata.paris.fr | web"
  } ]
}
```
Le plus simple est d'écrire un petit script Python temporaire qui lit `data/opendata-candidates.json`,
garde les `id` choisis, ajoute les événements trouvés sur le web, puis écrit `data/events.json`.

## 6. Validation
```bash
python3 scripts/validate.py
```
Le script nettoie le fichier (doublons, événements hors fenêtre, tri). S'il sort en erreur (❌),
corrige puis relance jusqu'à ce qu'il passe.

## 7. Publication
```bash
git add data/events.json
git commit -m "Mise à jour hebdo <start>"
git push origin main
```
Ne modifie aucun autre fichier du repo pendant une mise à jour hebdomadaire (pas même `data/opendata-candidates.json`).
Termine par un court résumé : le nombre d'événements par catégorie et les sources principales utilisées.
