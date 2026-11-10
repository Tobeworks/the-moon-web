# AGENTS.md

Verbindliche Regeln für Agents in `the-moon-web`.

- **Keinen Build ausführen** (`pnpm build`, `astro build` o. Ä.). Der Nutzer baut und prüft selbst.
- **Nichts committen.** Kein `git commit`, auch nicht mit Freigabe aus einer früheren Aufgabe.
- **Nichts pushen.** Kein `git push`, in keinem Repo.

- **Ist eine Änderung commit-reif, eine Commit-Message zurückgeben** (im Chat, nicht per `git commit`).

Änderungen bleiben im Working Tree. Committen und Pushen macht der Nutzer.

## Toolchain (`tools/`)

- `./tools/tmr generate|validate|convert|push|social <asset-ordner>` — Assets liegen in `../the-moon-assets/tmr-NNN-artist-title/`. `./tools/tmr studio` startet die lokale Oberfläche dafür. Details: [tools/README.md](tools/README.md).
- Ablauf: `push` lädt ans CDN und schreibt `data/releases.json` (Quelle der Wahrheit, mit Backup in `data/backups/`) → Nutzer committet (auch per Studio-Knopf, nur `data/releases.json`) und pusht → Build.
- **`push` geht nach außen** — nur nach ausdrücklicher Freigabe starten. `push` bricht nur bei `FILL_IN` in Artist/Titel/Katalog und fehlenden MP3s ab. Text, Datum und Links sind optional (ohne Text bleibt der Text leer).
- Plattformnamen sind an `src/assets/dsp/*.svg` gekoppelt: `spotify`, `apple_music`, `amazon_music`, `soundcloud`, `deezer`, `beatport`, `bandcamp`. Nie leere URLs eintragen; Scraper-Treffer nur mit `confidence ≥ 85` und passendem Künstler.
- Vor `release_date` blendet die Detailseite Plattform-Links aus („Releasing") — Absicht.
- Tests: `cd tools && source venv/bin/activate && python -m pytest tests`.
