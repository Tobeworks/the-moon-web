# Design: tmr studio, lokale Oberfläche für den Release-Ablauf

Datum: 2026-11-10 · Status: Entwurf, wartet auf Freigabe · Zielrepo: `the-moon-web` (Ordner `tools/`)

## 1. Zweck

Ein Release anzulegen kostet heute vor allem Handarbeit: Ordner anlegen, Dateien hineinkopieren, dann auf der Kommandozeile `generate`, `validate`, `convert` und `push` nacheinander aufrufen. Dabei geht der Überblick verloren: Welches Release steht in welchem Schritt, wann erscheint was, wo fehlen DSP-Links, ist `releases.json` schon committet?

**tmr studio** ist eine Oberfläche, die nur lokal im Browser läuft und diese Arbeit übernimmt. Sie ist eine dünne Schicht über der vorhandenen `tmr`-Toolchain. Dateien auswählen oder hineinziehen, Metadaten eintragen, konvertieren, hochladen und Links nachtragen geschieht an einer Stelle. Eine Übersicht zeigt für alle Releases, was noch offen ist.

Vorbild für Prinzip und Bedienung ist das Tool „Release Studio" (`/Users/tobe/Sites/logic-moon.de/youtube_movie_generator`): Python-Backend, Browser als Oberfläche, Projekte als Ordner, langlaufende Arbeit als Jobs mit Log.

## 2. Ausgangslage

- `the-moon-os` ist ins Web-Repo umgezogen (Submodule entfernt). Im Web-Repo liegen jetzt `data/releases.json`, `data/releases.schema.json` und `tools/` (`tmr`, `the-moon.py`, `commands/`, `setup.sh`, `requirements.txt`). Der Umzug ist im Working Tree erledigt, aber noch nicht committet.
- Die Toolchain ist ein `click`-Programm (`tools/the-moon.py`) mit den Befehlen `generate`, `validate`, `convert`, `social`, `push`, `sftp-test`. Die Befehle arbeiten auf einem Asset-Ordner `the-moon-assets/tmr-NNN-artist-title/` (mit `audio/` und `artwork/`) und drucken ihre Ausgabe auf stdout. Bei Fehlern beenden sie sich mit `sys.exit(1)`.
- `push` lädt per SFTP auf das CDN und schreibt den Eintrag in `data/releases.json`. Die Zugangsdaten (`CDN_HOST`, `CDN_USER`, `CDN_PASSWORD` und weitere) liest es aus einer `.env` im Repo-Root (`push.py`, `load_env`).
- DSP-Links holt der externe `dsp_scraper` (`/Users/tobe/Sites/logic-moon.de/dsp_scraper`), Aufruf `uv run python cli.py "<bandcamp-url>" --stdout`.
- Quelle der Wahrheit für den Katalog ist `data/releases.json`. Die Website liest sie direkt.

## 3. Ziele

1. **Ordner und Dateien ohne Handarbeit.** Release anlegen erzeugt die Ordnerstruktur. Audio und Cover kommen per Dateidialog, Ordnerdialog oder Drag & Drop an die richtige Stelle.
2. **Der ganze Ablauf an einer Stelle.** Anlegen, Metadaten, Validieren, Konvertieren, Push ans CDN, DSP-Links nachtragen, jeweils mit sichtbarem Fortschritt und Log.
3. **Überblick über den Katalog.** Eine Tabelle aller Releases mit Erscheinungsdatum („in 3 Tagen"), Fortschritt pro Schritt und dem jeweils nächsten Schritt als Knopf.
4. **Fehler verhindern, die bisher still passieren.** Plattformnamen kommen aus fester Liste, leere URLs werden nie angelegt, ein unveränderter Platzhalter-`about.md` sperrt den Push, ein Cover, das neuer ist als die MP3s, schlägt `--force` vor, ein nicht committetes `releases.json` ist sichtbar.
5. **Optisch einheitlich mit der Website** (Moon Sand, Josefin Sans, Space Mono), siehe Abschnitt 8.

## 4. Nicht-Ziele und Anti-Ziele

- **Nicht-Ziele:**
  - Kein Hosting. Die Oberfläche läuft nie auf dem Server und gehört nicht ins Docker-Image.
  - Keine zweite Datenbank neben `releases.json`.
  - Kein Mailversand und keine Promo-Mails (laufen über die Website).
  - Keine Git-Schreibzugriffe: kein Commit, kein Push, kein Submodule-Handling.
  - Kein Umbau der vorhandenen Befehle. Die CLI muss unverändert weiter funktionieren.
  - Kein Build-Setup für das Frontend (kein Vite).
  - Keine Windows- oder Linux-Unterstützung. Das Tool läuft nur auf macOS.
- **Anti-Ziele (dann ist es gescheitert, auch wenn es technisch läuft):**
  - Ein Upload ans CDN ohne ausdrückliche Bestätigung im Moment des Klicks.
  - Ein Eintrag in `releases.json`, der von der Toolchain nicht validiert wurde, oder ein Schreibzugriff darauf ohne Backup.
  - Zwei Wahrheiten, die auseinanderlaufen (zum Beispiel ein eigener Statusspeicher, der nicht zum Dateizustand passt).
  - Eine Oberfläche, die nur kleiner und schlechter ist als die Kommandozeile.

## 5. Entscheidungen von Tobias

- Die Oberfläche ist nur eine Hilfe für die **lokale** Arbeit: Dateien kopieren, Releases anlegen, JSON schreiben, konvertieren, pushen.
- Technisch nach dem Vorbild Release Studio: Python-Backend, Browser-Oberfläche.
- **Look von the-moon-web übernehmen**, damit beides einheitlich wirkt.
- Dateien über **Dateidialog und Ordnerdialog** auswählen können, zusätzlich zu Drag & Drop.
- **Alles größer und weitläufiger** als im ersten Mockup, keine kleinen Schriften (Details in Abschnitt 8).
- Eine **Übersicht** über alle Releases mit Erscheinungsterminen und Fortschritt ist wichtig. Ob dafür eine „kleine Datenbank" nötig ist, hat er offen gelassen (siehe Abschnitt 6, Statusermittlung).
- Der **Mockup** in `.superpowers/brainstorm/90220-1794299630/content/ui-layout-v2.html` zeigt die gewünschte Richtung und Aufteilung (Übersicht, Release-Detail, Neu anlegen). Er gilt für Struktur und Look, nicht für Schriftgrößen.

## 6. Entwurf

### Aufbau

- Ordner `tools/studio/`: ein FastAPI-Server (`server.py`) und eine einzelne Seite (`index.html`) ohne Build-Schritt.
- Start über einen neuen Befehl `./tools/tmr studio`. Er startet den Server, öffnet den Browser und gibt die Adresse im Terminal aus. Beenden mit Strg+C.
- Der Server bindet **nur an `127.0.0.1`** und verlangt bei jedem Aufruf ein beim Start erzeugtes Token (in der geöffneten Adresse enthalten). Grund: Das Tool kann Dateien schreiben und hochladen, eine fremde Webseite im selben Browser darf es nicht ansteuern.
- Neue Abhängigkeiten in `tools/requirements.txt`: `fastapi`, `uvicorn`, `python-multipart`.

### Befehle ausführen

Das Backend ruft die vorhandenen Befehle als **Unterprozess** auf (`./tools/tmr convert <pfad>` und so weiter) und streamt stdout zeilenweise an die Seite (Server-Sent Events). Damit bleibt die CLI die einzige Implementierung, und jede Aufgabe lässt sich auch im Terminal nachstellen. Der Exit-Code entscheidet über Erfolg oder Fehler.

Es läuft immer nur ein Job gleichzeitig. Schließt man den Tab, läuft der Job weiter. Beim erneuten Öffnen sieht man seinen Log und Stand.

### Statusermittlung (ohne eigene Datenbank)

Der Status eines Releases wird bei jedem Laden aus dem Dateizustand berechnet. Quellen sind `data/releases.json`, die Ordner in `the-moon-assets` und `git status`.

| Schritt | Kürzel | Gilt als erledigt, wenn |
|---|---|---|
| Assets | A | Ordner `tmr-NNN-…` mit mindestens einer Audiodatei in `audio/` und einem Cover in `artwork/` existiert |
| Validiert | V | `release.json` ist vorhanden, `validate` läuft ohne Fehler, und `about.md` ist nicht mehr der Platzhalter des Generators |
| Konvertiert | K | für jeden Track gibt es MP3 in 320k und 128k in `export/`, und das Cover ist nicht neuer als die MP3s (sonst „veraltet", mit Hinweis auf `--force`) |
| Gepusht | P | `data/releases.json` enthält einen Eintrag für den Katalog mit `pushed_at` |
| Git | G | `data/releases.json` hat keine nicht committeten Änderungen (nur Anzeige, das Tool committet nicht) |
| DSP-Links | D | `platforms` enthält mit nicht-leerer URL mindestens `spotify`, `apple_music`, `amazon_music` und `deezer` (`beatport` optional) |

Der Asset-Ordner eines Releases wird über den Katalog gefunden (`TMR-018` entspricht dem Ordner, der mit `tmr-018-` beginnt). Gibt es für ein bereits gepushtes Release keinen Asset-Ordner (ältere Releases), zeigt die Oberfläche A, V und K als „–" (nicht anwendbar) und nicht als offen. Solche Releases erscheinen nicht in den Kennzahlen „offene Schritte".

„Demnächst" ist ein Release, dessen `release_date` in der Zukunft liegt. Die Tabelle ist nach Datum absteigend sortiert. Die Kopfzeile zeigt, ob `releases.json` nicht committet ist, und einen Commit-Message-Vorschlag zum Kopieren.

### Ansichten

1. **Übersicht.** Kennzahlen (gesamt, demnächst, offene Schritte, ohne DSP-Links) und die Tabelle der Releases mit sechs Fortschrittskästchen und Knopf „nächster Schritt". Ein Klick auf eine Zeile öffnet das Detail.
2. **Release-Detail.** Links die Schrittleiste, rechts je ein Panel:
   - *Assets:* Drag & Drop plus „Dateien wählen …", „Ordner wählen …", „Cover wählen …". Liste der vorhandenen Dateien mit Format und Größe.
   - *Metadaten:* Formular für Artist, Titel, Katalog, Datum, `about.md` (Editor). Schreibt `release.json` und `about.md` und führt `validate` aus.
   - *Konvertieren:* Knopf, Option `--force` (vorgeschlagen, wenn das Cover neuer ist), Fortschrittsbalken und Log.
   - *Push ans CDN:* Der Knopf öffnet eine Zusammenfassung (Dateien, Gesamtgröße, Ziel) und verlangt eine Bestätigung. Er ist gesperrt, solange V oder K nicht erfüllt sind.
   - *DSP-Links:* Führt den Scraper aus, wenn eine Bandcamp-URL im Release steht. Zeigt Treffer mit Plattform, URL, Confidence und Künstlername.
3. **Neu anlegen.** Katalognummer (nächste freie wird vorgeschlagen), Artist, Titel, Datum. Legt den Ordner `tmr-NNN-artist-title/` mit `audio/` und `artwork/` an, auf Wunsch gleich mit Dateien. Ruft anschließend `generate` auf.

### Dateien übernehmen

- **Dateidialog und Ordnerdialog** öffnen den nativen macOS-Dialog über das Backend (`osascript`). Das Backend erhält Pfade auf der Festplatte und **kopiert direkt**, ohne Umweg über den Browser. Das ist bei WAVs von mehreren 10 MB der schnellere Weg.
- **Drag & Drop** liefert im Browser keine Pfade, die Datei wird deshalb per Upload an das Backend übertragen und dort direkt in den Zielordner gestreamt (nie komplett im Speicher).
- Beides legt Audiodateien in `audio/` und das Cover in `artwork/`. Vorhandene Dateien werden nie stillschweigend überschrieben: bei gleichem Namen fragt die Oberfläche nach.

### DSP-Links

- Vorbedingung ist eine Bandcamp-URL in `platforms`. Fehlt sie, zeigt das Panel einen Hinweis und ein Eingabefeld.
- Vorgeschlagen werden nur Treffer mit `confidence ≥ 85` **und** vorhandenem `matched_artist`. Schwächere Treffer werden als „prüfen" markiert und nur auf ausdrücklichen Klick übernommen.
- Plattformnamen kommen aus der festen Liste `spotify`, `apple_music`, `amazon_music`, `soundcloud`, `deezer`, `beatport`, `bandcamp` (entspricht den Logo-Dateien in `src/assets/dsp/`). Kein Treffer bedeutet kein Eintrag. Es werden nie leere URLs angelegt.
- Übernommene Links werden an die Liste `platforms` angehängt. Vorhandene Einträge bleiben unverändert.

### Schreibzugriffe auf `data/releases.json`

Jede Änderung durch das Tool (Push, DSP-Links, Metadaten bearbeiten) legt vorher ein Backup an, wird gegen `data/releases.schema.json` geprüft und erst dann geschrieben. Bei einem Schemafehler bleibt die Datei unverändert und die Oberfläche zeigt den Fehler.

## 7. Randbedingungen

- **Regeln für Agents im Web-Repo** (`AGENTS.md`): keinen Build ausführen, nichts committen, nichts pushen. Für den, der dieses Tool baut, gilt das weiter.
- **Aktionen nach außen** (CDN-Upload) brauchen im Tool die Bestätigung direkt vor der Ausführung. Eine frühere Freigabe gilt nicht fort.
- **CDN-Zugangsdaten:** Sie stehen derzeit in der `.env` des alten OS-Repos (Schlüssel `CDN_HOST`, `CDN_PROTOCOL`, `CDN_PORT`, `CDN_USER`, `CDN_PASSWORD`, `CDN_BASE_PATH`, `CDN_PUBLIC_URL`). Die `.env` des Web-Repos enthält sie nicht, `push` bricht deshalb ab, bis Tobias diese Schlüssel dorthin übernommen hat. Das Tool soll das beim Start melden und Passwörter nie anzeigen oder loggen.
- **Docker:** `tools/` ist in `.dockerignore` ausgeschlossen. Das Tool darf nichts brauchen, was für den Website-Build nötig ist.
- **Repo-Nachbarn:** Das Tool erwartet `the-moon-assets` und `dsp_scraper` als Nachbarordner. Die Pfade stehen an einer Stelle und lassen sich überschreiben.

## 8. Oberfläche

- Look aus `src/styles/global.css`: Hintergrund `#0C0C0C`, Flächen `#141414` bis `#252525`, Text `#E8E4D8`, Akzent „Moon Sand" `#C4B98A`. Schriften Josefin Sans (Beschriftung und Text) und Space Mono (Zahlen, Pfade, Log). Dieselbe Schriftquelle wie die Website verwenden.
- **Größen:** Das erste Mockup war zu klein. Vorgabe: Fließtext mindestens 18 px, Tabellenzeilen und Formularfelder mindestens 48 px hoch, kleinste Beschriftung 14 px. Abstände großzügig, mindestens 24 px zwischen Panels, Klickflächen mindestens 44 px. Das Layout darf auf 1200 px Breite beschränkt bleiben.
- Farben für Status: erledigt grün, nächster Schritt Sand, Warnung orange, offen grau. Status nie nur durch Farbe, immer auch durch Buchstabe oder Text.

## 9. Was dem Bauenden überlassen bleibt

- Aufbau von `server.py` (Module, Routen) und die Wahl der kleinen Frontend-Bibliothek (Vue, Alpine oder Vanilla), solange es **keinen Build-Schritt** gibt und die Datei offline lauffähig ist (Bibliothek lokal ablegen, nicht von einem CDN laden).
- Wie genau der Platzhalter-`about.md` erkannt wird (aus `generate.py` ableiten).
- Das Format der Aufteilung zwischen Statusfunktion und Routen.
- **Tests (Entscheidung von Tobias: Unit-Tests wie bei Release Studio):** pytest in `tools/tests/`, temporäre Ordner statt echter Releases, kein Netzwerk. Die Statusfunktion bekommt Tests für alle sechs Schritte (erledigt, offen, veraltet, nicht anwendbar). Die API wird mit dem FastAPI-`TestClient` getestet. Ein Test darf nie das CDN erreichen oder `data/releases.json` im Repo verändern. End-to-End-Tests mit Playwright (installiert) sind **nicht Teil von Phase 1**. Ein einzelner Rauchtest ist später möglich, wenn die Oberfläche steht.
- Feinheiten der Oberfläche innerhalb der Vorgaben aus Abschnitt 8.

## 10. Aufgeteilt in Phasen

0. **Phase 0 (erledigt, uncommittet): CLI absichern.** Die Prüfungen liegen in der CLI und nicht nur in der Oberfläche. Das Studio verlässt sich auf Exit-Codes und auf diese Sperren.
   - `push` bricht vor dem Upload ab, wenn Platzhalter (`FILL_IN`, `YYYY-MM-DD`, Platzhalter-`about.md`) vorhanden sind oder `CDN_PUBLIC_URL` fehlt.
   - Ein erneuter Push behält vorhandene DSP-Links und manuelle Felder, ersetzt den Eintrag an seiner Position und schreibt `releases.json` nur nach Schemaprüfung, mit Backup (`data/backups/`) und atomar.
   - `convert` endet bei Fehlern mit Exit-Code 1, bettet das Cover als 1500-px-JPEG ein statt als 3000-px-Master und warnt, wenn das Cover neuer ist als die MP3s.
   - `generate` behält Handarbeit (Tracktitel, `year`, `genre`) und bricht bei unlesbaren Audiodateien ab.
   - `validate` lehnt `FILL_IN` und Platzhalter-`about.md` ab und akzeptiert PNG, JPG und TIFF als Cover.
   - Entfernt: `push --preview-only` (nie funktionsfähig) und `push-all.sh`.
   - Tests: `tools/tests/` (pytest), Aufruf `cd tools && source venv/bin/activate && python -m pytest tests`.
1. **Phase 1:** Server, Übersicht, Neu anlegen, Dateien übernehmen, Metadaten, Validieren, Konvertieren, Push mit Bestätigung. Das deckt den beschriebenen Alltag ab.
2. **Phase 2:** DSP-Links per Scraper, Social-Assets (`tmr social`).
3. **Später, nicht Teil dieses Designs:** `.app`-Starter fürs Dock, Windows/Linux.

## 11. Annahmen von Claude (bitte prüfen)

Diese Punkte hat Tobias nicht entschieden, sie sind eine Einschätzung:

- Name **tmr studio** und Ablage unter `tools/studio/`.
- Befehl `./tools/tmr studio` statt einem getrennten Programm.
- **Bestehendes `venv` und `setup.sh` bleiben**, es kommen nur drei Pakete dazu. `uv` wird nicht eingeführt.
- **Unterprozesse statt Funktionsaufrufe** für die Befehle, weil diese `print` und `sys.exit` verwenden.
- Token und `127.0.0.1` als Schutz gegen fremde Seiten im selben Browser.
- Als „DSP komplett" gelten `spotify`, `apple_music`, `amazon_music`, `deezer`.
- Das Tool committet nie selbst, es zeigt nur den Zustand und einen Commit-Message-Vorschlag.
- Phase 2 (DSP-Scraper, Social) kommt nach dem Kern.
- Nur macOS (wegen `osascript` für die Dialoge).
