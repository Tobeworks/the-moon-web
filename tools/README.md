# The Moon Records, Toolchain und Studio

Alles für den Release-Ablauf: Ordner anlegen, Dateien übernehmen, Metadaten pflegen,
konvertieren, ans CDN hochladen, DSP-Links nachtragen.

Es gibt zwei Wege, die dasselbe tun:

- **Studio**: lokale Oberfläche im Browser (`./tools/tmr studio`). Der bequeme Weg.
- **CLI**: `./tools/tmr <befehl> <asset-ordner>`. Das Studio ruft genau diese Befehle auf.

---

## 1. Einrichtung (einmalig)

```bash
bash tools/setup.sh                 # legt tools/venv an und installiert alles
brew install ffmpeg                 # falls noch nicht vorhanden (MP3-Konvertierung)
```

Voraussetzungen im Dateisystem:

| Was | Wo |
|---|---|
| Web-Repo (dieses Repo) | `…/The Moon/the-moon-web` |
| Asset-Ordner der Releases | `…/The Moon/the-moon-assets` (Nachbarordner) |
| DSP-Scraper (nur für DSP-Links) | `/Users/tobe/Sites/logic-moon.de/dsp_scraper`, braucht `uv` |
| CDN-Zugang | Datei `.env` im Repo-Root mit `CDN_HOST`, `CDN_PROTOCOL`, `CDN_PORT`, `CDN_USER`, `CDN_PASSWORD`, `CDN_BASE_PATH`, `CDN_PUBLIC_URL` |

Abweichende Pfade: Umgebungsvariablen `TMR_ASSETS_DIR` und `TMR_SCRAPER_DIR`.

Verbindung zum CDN testen (lädt nichts hoch):

```bash
./tools/tmr sftp-test
```

---

## 2. Studio starten

```bash
./tools/tmr studio                  # öffnet den Browser
./tools/tmr studio --no-open        # nur die Adresse ausgeben
./tools/tmr studio --port 8800      # anderer Port (Standard 8777, sonst der nächste freie)
```

- Im Terminal erscheint eine Adresse wie `http://127.0.0.1:8777/?key=…`. Der Schlüssel
  ist bei jedem Start neu. Ohne ihn lässt der Server nichts zu.
- **Beenden:** `Strg+C` im Terminal. Ein laufender Job bricht dabei ab.
- Das Studio läuft nur auf deinem Rechner (`127.0.0.1`) und nie auf dem Server.

---

## 3. Bedienung

### Übersicht

Eine Zeile pro Release, neueste zuerst. Releases, die nur als Ordner existieren
(noch nicht gepusht), stehen mit dabei.

Sechs Kästchen zeigen den Stand:

| | Schritt | erledigt, wenn |
|---|---|---|
| **A** | Assets | Audio in `audio/` und Cover in `artwork/` liegen im Ordner |
| **V** | Daten | Artist, Titel, Datum, Cover-Name stehen drin, `about.md` ist geschrieben, alle Audiodateien da |
| **K** | Konvertiert | MP3 (128k und 320k) für jeden Track vorhanden |
| **P** | Gepusht | Eintrag in `data/releases.json` mit `pushed_at` |
| **G** | Git | Eintrag entspricht dem letzten Commit von `data/releases.json` |
| **D** | DSP-Links | `spotify`, `apple_music`, `amazon_music`, `deezer` mit URL eingetragen |

Symbole: `✓` erledigt, `·` offen, `!` prüfen (zum Beispiel nicht committet), `↻` veraltet
(Cover ist neuer als die MP3s), `–` nicht anwendbar (ältere Releases ohne Asset-Ordner).
Das hervorgehobene Kästchen ist der nächste Schritt. Der Knopf rechts springt direkt dorthin.

Ein Klick auf eine Zeile öffnet das Release.

### Neues Release anlegen

**Neu anlegen** → Katalognummer (wird vorgeschlagen), Datum, Artist, Titel → **Anlegen**.
Das erzeugt `the-moon-assets/tmr-NNN-artist-title/` mit `audio/` und `artwork/`.

### Release bearbeiten (Reihenfolge von oben nach unten)

1. **Assets**: WAVs und Cover mit **Dateien wählen …**, **Ordner wählen …** oder
   **Cover wählen …** (macOS-Dialog, kopiert direkt) oder per Drag & Drop in die Fläche ziehen.
   Gibt es eine Datei schon, wirst du gefragt, ob sie überschrieben werden soll.
2. **Metadaten**: Artist, Titel, Datum, Genre, Bandcamp-URL und den Releasetext (`about.md`) eintragen →
   **Speichern**. Danach **Tracks einlesen** (liest Titel und Länge aus den Audiodateien, eigene
   Tracktitel bleiben erhalten) und **Validieren**.
   Der Text in `about.md` landet auf der Website. Der Platzhalter-Text sperrt den Push.
   **Text mit KI schreiben** erzeugt einen Entwurf (Claude, `ANTHROPIC_API_KEY` in der `.env`). Optional
   Stichworte dazu schreiben. Der Entwurf landet nur im Textfeld und wird erst mit **Speichern** übernommen.
   Gesendet werden Titel, Tracknamen, Stichworte, der aktuelle Text und drei ältere Releasetexte als Stilvorlage.
3. **Konvertieren**: erzeugt MP3 in 128k (Web-Player) und 320k (Download) und die Cover-Varianten.
   Hast du das Cover geändert, ist **Überschreiben** schon angehakt. Sonst behalten die MP3s das alte Bild.
   Der **Fortschrittsbalken** unter der Kopfzeile zeigt, wie weit Konvertieren und Push sind. **Abbrechen**
   stoppt die Aufgabe. Unter **Anhören** spielst du die Tracks ab (WAV-Original, sonst 320k-MP3).
4. **Push ans CDN**: **Freigeben und hochladen …** öffnet eine Zusammenfassung (Dateien, Größe, Ziel).
   Zum Starten musst du die Katalognummer eintippen. Der Push lädt hoch und schreibt den Eintrag in
   `data/releases.json`. Davor entsteht ein Backup in `data/backups/`.
   Ein erneuter Push behält vorhandene DSP-Links und manuell ergänzte Felder.
5. **DSP-Links** (erst nach dem Push, meist Wochen später): **Links suchen** fragt den Scraper über die
   Bandcamp-URL ab. Vorausgewählt sind nur Treffer ab Confidence 85 mit passendem Künstler. Mit `!`
   markierte Treffer prüfst du selbst und hakst sie bei Bedarf an. **Ausgewählte übernehmen** trägt sie ein.

Unten auf der Seite zeigt das **Protokoll** die Ausgabe des laufenden Befehls.
Es läuft immer nur ein Job gleichzeitig.

### Nach dem Push: Git

Nach einem Push (oder nach übernommenen DSP-Links) zeigt das Studio `!` bei **G** und oben ein
Feld **releases.json committen** mit vorbelegter Nachricht (änderbar). **Committen** committet
**nur `data/releases.json`**, lokal. Andere Dateien bleiben unberührt.

Das Studio **pusht nie** zu GitHub. Das machst du selbst im Terminal:

```bash
git push
```

Erst dieser Push des Web-Repos löst den Website-Build aus.

### Typischer Ablauf

Neu anlegen → Dateien → Metadaten speichern → Tracks einlesen → Validieren → Konvertieren →
Push → committen (Studio) → `git push` (Terminal) → Wochen später DSP-Links.

---

## 4. Gesperrter Push, was heißt das?

Der Knopf ist grau, wenn eine der Meldungen darunter steht (auch im Panel Metadaten und im Push-Dialog):

| Meldung | Ursache |
|---|---|
| `Artist fehlt`, `Titel fehlt`, `Katalognummer fehlt` | unter Metadaten ausfüllen und speichern |
| `Keine Tracks …` | Audiodateien hinzufügen, dann **Tracks einlesen** |
| `Noch nicht konvertiert` | erst Konvertieren |
| `Cover ist neuer als die MP3s` | Konvertieren mit **Überschreiben** |
| `missing in .env: …` | CDN-Schlüssel in der `.env` im Repo-Root fehlen |

Mehr braucht der Push nicht. **Kein** Hindernis sind Releasetext, Release-Datum, Cover-Name, Genre
und Plattform-Links (auch keine Bandcamp-URL). Dazu zeigt das Studio nur **Hinweise**. Ohne Text
bleibt der Text auf der Website leer, ein Platzhalter-Text wird nie veröffentlicht. Ohne Datum gilt
das Release sofort als veröffentlicht.

---

## 5. CLI ohne Studio

```bash
./tools/tmr generate <asset-ordner>              # release.json aus den Audiodateien (behält Handarbeit)
./tools/tmr validate <asset-ordner>              # volle Prüfung (strenger als der Push; --generate-md schreibt release_draft.md)
./tools/tmr convert  <asset-ordner> [--force]    # WAV/AIFF → MP3 128k + 320k, ID3-Tags, Cover-Varianten
./tools/tmr push     <asset-ordner>              # CDN-Upload + data/releases.json (geht nach außen!)
./tools/tmr social   <asset-ordner> --init       # social.json anlegen, dann bearbeiten
./tools/tmr social   <asset-ordner> --format square|reel|all [--duration 30]
./tools/tmr sftp-test                            # CDN-Verbindung prüfen, ohne Upload
```

- Alle Befehle brechen mit Exit-Code 1 ab, wenn etwas nicht stimmt.
- Das Cover wird in die MP3s als 1500-px-JPEG eingebettet (nicht als 3000-px-Master).
- `social` rendert nach `<asset-ordner>/export/social/<format>/` (Details in `commands/social.py`).
  Im Studio gibt es dafür noch keinen eigenen Knopf.

### Asset-Ordner

```
the-moon-assets/tmr-018-artist-title/
├── audio/            WAV/AIFF-Quellen
├── artwork/          Cover (PNG/JPG/TIFF, mindestens 3000×3000)
├── export/
│   ├── mp3/128/ und mp3/320/
│   ├── artwork/      cover_3000/1500/600/300 als JPG und WebP
│   └── social/
├── release.json      Metadaten (Quelle für den Push)
├── about.md          Releasetext
└── social.json       optional
```

---

## 6. Fehlerbehebung

| Problem | Lösung |
|---|---|
| `venv not found` | `bash tools/setup.sh` |
| `ModuleNotFoundError` im Studio | `source tools/venv/bin/activate && pip install -r tools/requirements.txt` |
| Port belegt | wird automatisch der nächste freie genommen (Standard 8777; 8765 gehört Release Studio), oder `--port` setzen |
| Oben rechts `CDN: .env unvollständig` | `.env` im Repo-Root ergänzen (Schlüssel siehe Abschnitt 1) |
| DSP-Suche schlägt fehl | Bandcamp-URL eingetragen? `uv` installiert? Pfad des Scrapers prüfen (`TMR_SCRAPER_DIR`) |
| `releases.json NOT written — schema violation` | Eintrag verletzt `data/releases.schema.json`, die Datei bleibt unverändert |
| Alte Version von `releases.json` zurückholen | Backups liegen in `data/backups/` (nicht in Git) |

---

## 7. Tests und Aufbau

```bash
cd tools && source venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests
```

| Pfad | Inhalt |
|---|---|
| `tools/the-moon.py`, `tools/tmr` | CLI-Einstieg |
| `tools/commands/` | `generate`, `validate`, `convert`, `push`, `social`, gemeinsame Prüfungen (`checks.py`) |
| `tools/studio/` | `status.py` (Stand berechnen), `folders.py` (Ordner, Dateien, Metadaten), `jobs.py`, `dsp.py`, `server.py` (API), `index.html` (die ganze Oberfläche) |
| `tools/tests/` | Tests, nutzen nur Temp-Ordner und erreichen nie das CDN |

Design und Plan: `docs/superpowers/specs/2026-11-10-tmr-studio-design.md`,
`docs/superpowers/plans/2026-11-10-tmr-studio.md`.

---

## 8. Eigenständiges Werkzeug

`tools/the-moon-vhs.sh input.mp4 [output.mp4]` legt den VHS-Look des Labels (Scanlines, Grain,
Vignette, Farbkorrektur) per FFmpeg über ein Video. Braucht nur `ffmpeg`, nicht das venv.
