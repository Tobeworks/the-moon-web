# Spec: Features aus logicmoon_astro nach the-moon-web übernehmen

Datum: 2026-10-29 · Status: offen · Zielrepo: `the-moon-web`

## 1. Zweck und Kontext

In `logicmoon_astro` (logic-moon.de) sind in den letzten Commits mehrere Dinge entstanden, die auch auf the-moon-records.de sinnvoll sind. Dieses Dokument beschreibt sie so, dass ein Agent sie im Zielrepo umsetzen kann, ohne die Session zu kennen.

- **Quellrepo:** `/Users/tobe/Sites/logic-moon.de/logicmoon_astro` (Astro 7, Vue, Tailwind 4, pnpm). Lies dort die genannten Dateien als Referenz, kopiere sie aber nicht blind.
- **Relevante Quell-Commits:** `bd60b6a` (Release-Landingpage), `c65d3d4` (Social Sharing), `8fea280` / `746503d` / `891b2d8` (Mobile-Optimierung), `3e63c76` (Auto-Bumper). Die Änderungen stehen mit `git show <hash>` im Quellrepo.
- **Regeln im Zielrepo (aus `AGENTS.md`):** Keinen Build ausführen. Nichts committen, nichts pushen. Ist eine Änderung commit-reif, die Commit-Message im Chat zurückgeben.

## 2. Umfang

**In Scope** (jeweils ein eigener Abschnitt unten):

1. Release-Landingpage mobil neu aufbauen
2. Share-Buttons mit Instagram-Story-Bild und Facebook-Link
3. Link-Vorschaubild (Open Graph) 1200×630 pro Release
4. Strukturierte Daten (JSON-LD) für Releases
5. Vorherige/nächste Release als echte Links
6. Footer neu (Social-Icons in eigener Spalte, mobil kompakt)
7. Header und mobile Navigation kompakter, Seitenränder bündig
8. Allgemeine Mobile-Regeln für alle Seiten
9. Auto-Bumper für die Version

**Out of Scope (bewusst nicht übernehmen):** Sea-of-Grey-Blogartikel, Favicon (hat the-moon-web ein eigenes), DSP-Scraper, Release-Daten von logic-moon.de, das optionale Feld `post` (Verlinkung auf Blogartikel, the-moon-web hat keinen Blog), Modal-Entfernung (gibt es hier nicht).

## 3. Unterschiede der Zielumgebung (zuerst prüfen)

| Thema | logicmoon_astro (Quelle) | the-moon-web (Ziel) |
|---|---|---|
| Release-Daten | `src/releases.js`, Felder `slug`, `cover`, `year`, `title` ("Artist - Titel"), Plattform-Keys `bandcamp`, `spotify`, ... | `the-moon-os/data/releases.json`: `catalog`, `artist`, `title`, `year`, `artwork`, `cover`, `tracks`, `platforms[]` (`{name, url}`), `release_date` |
| Release-Seite | statisch (`getStaticPaths`) | `src/pages/releases/[slug].astro` mit `prerender = false` (SSR, Node-Adapter) |
| Titel | ein String "Artist - Titel", muss gesplittet werden | `artist` und `title` schon getrennt, kein Split nötig |
| Design-Tokens | `surface`, `primary`, `on-surface` ... | `bg`, `surface`, `fg`, `fg-dim`, `fg-muted`, `accent`, `border`; Schriften `font-label` (Josefin Sans) und `font-mono` (Space Mono) |
| Basisgröße | `rem` = 16 px | `html { font-size: 120% }`, also `rem` = 19,2 px. Alle rem-Werte aus diesem Dokument deshalb nachrechnen (px ÷ 19,2) |
| Plattform-Logos | Simple Icons plus eigene SVGs | `src/assets/dsp/*.svg` (`DspLinks.astro`, SVGs nutzen `currentColor`) |
| Icons | `simple-icons` (Dependency) | `lucide-astro`, kein `simple-icons` |
| JSON-LD | vorhanden | noch nicht vorhanden |
| Husky | vorhanden | nicht vorhanden |
| Astro | 7 | 6 |
| `sharp` | Dependency | in `pnpm-workspace.yaml` erlaubt (`sharp: true`) |

**Regel für alle Abschnitte:** Verhalten und Aufbau übernehmen, aber mit den Tokens, Schriften und Konventionen von the-moon-web umsetzen. Texte im Zielrepo nicht erfinden: Social-Links aus vorhandenen Links ableiten.

## 4. Release-Landingpage mobil

**Ziel:** Alles kompakter und eindeutig gegliedert. Quelle: `src/pages/discography/[slug].astro`.

Die Seite hat bereits einen eigenen Mobile-Block (`sm:hidden`). Auf diese Prinzipien umbauen:

- **Oberer Block als Karte:** Cover links (ca. 9 rem bei 16 px Basis, im Ziel ca. 7,5 rem), rechts Artist als kleines Label, Titel groß, Jahr klein darunter. Zeilenfolge: Back-Link (min. 44 px hoch), dann die Karte.
- **Zwei beschriftete Zeilen untereinander:**
  - "Listen on" mit den Plattform-Logos (umrandete 44-px-Kacheln).
  - "Share" mit den Share-Buttons (gefüllte 44-px-Kacheln, ohne Rahmen). Zwischen beiden eine feine Trennlinie. Man muss auf einen Blick erkennen, was Plattform ist und was Share.
- **Desktop unverändert lassen.** Alles über `md:`/`sm:`-Präfixe, die Desktop-Klassen bleiben.
- **Player:** mobil schlank (nur Player, ohne Tracklist), ab Tablet voll. Wo das Bandcamp-Embed benutzt wird, zwei `iframe`s mit `loading="lazy"` und `hidden md:block` / `md:hidden`; versteckte lazy-iframes laden nicht. Im Ziel ist der Player der eigene `AudioPlayer`: dort nur Abstände und Größen kompakter machen.
- **Weitere Releases:** mobil Zeilen (Cover 56 px, Titel, Jahr), ab Tablet das 4er-Raster.
- **Vertikaler Rhythmus mobil:** Seitenränder eine einzige Größe (siehe Abschnitt 7), Abstände zwischen Abschnitten halbiert.

**Abnahme:** Bei 360, 390 und 1440 px Breite kein horizontaler Überlauf; Back-Link, Logo und Burger liegen auf derselben linken Kante (gemessen).

## 5. Share-Buttons (Instagram-Story und Facebook)

**Ziel:** Auf der Release-Seite zwei Buttons: "Instagram-Story" (Bild für die Story vorbereiten) und "Facebook" (Link teilen). Quelle: `src/components/ShareButtons.astro`.

**Facebook:** einfacher Link, `https://www.facebook.com/sharer/sharer.php?u=<encodeURIComponent(kanonische Release-URL)>`, `target="_blank" rel="noopener noreferrer"`. Facebook zieht Titel und Bild aus den OG-Tags (Abschnitt 6).

**Instagram-Story:** Ein Button, der im Browser ein Bild erzeugt:
- Canvas **1080×1920**, Export als **JPEG** (`canvas.toBlob(..., "image/jpeg", 0.92)`), Dateiname `<slug>-story.jpg`.
- Aufbau (Koordinaten aus der Quelle, in Canvas-Pixeln): Hintergrund in der Seitenfarbe; Cover 880×880 mittig bei y=250; Artist-Zeile (Versalien, Zeichenabstand, 32 px) bei Grundlinie 1230; Titel (Versalien, fett, 72 px, max. 3 Zeilen, Zeilenabstand 84 px) ab Grundlinie 1330; darunter eine Reihe Plattform-Logos (64 px, Abstand 48 px, mittig, Farbe wie die Labels) 90 px unter der letzten Titelzeile; ganz unten Jahr und Domain als kleine Zeile. Farben aus den CSS-Variablen lesen (`getComputedStyle`), keine festen Hex-Werte.
- **Kein "OUT NOW"** schreiben: Es stimmt für ältere Releases nicht. Besser Jahr und Domain.
- **Plattform-Logos auf dem Bild:** nur Plattformen mit vorhandenem Link, gleiche Reihenfolge wie auf der Seite. SVG-Strings serverseitig vorbereiten (in Frontmatter/Helper), als JSON in `data-icons` am Button, im Client `currentColor` durch die Zielfarbe ersetzen, `width`/`height` setzen und als `data:image/svg+xml`-Bild ins Canvas zeichnen. Eine SVG ohne `xmlns`-Attribut funktioniert nicht als Bild und muss ergänzt werden (`xmlns="http://www.w3.org/2000/svg"`).
- **Teilen:** Wenn `navigator.canShare({ files: [file] })` true ist, `navigator.share({ files: [file] })`. Ein `AbortError` (Menü geschlossen) ist kein Fehler. Bei jedem anderen Fehler oder wenn Teilen nicht möglich ist: Datei per `<a download>` und `URL.createObjectURL` herunterladen.
- **Wichtig für iOS/Safari:** `share()` muss direkt im Tap laufen. Deshalb das Bild **schon beim Laden der Seite** erzeugen (Promise merken, bei Fehler neu versuchen) und im Click nur noch `await` auf das fertige File.
- **Web Share braucht https** (oder `localhost`). Über `http://<LAN-IP>` fehlt `navigator.canShare`, dann greift der Download. Zum Testen am Handy also eine https-Adresse.
- Die Instagram-API kann keine Story direkt anlegen und keinen Link-Sticker setzen. Die Adresse steht deshalb im Bild.
- Schrift: erst `document.fonts.load(...)` für die verwendeten Schnitte abwarten, dann zeichnen.
- Touch-Ziel 44×44 px, `aria-label` und `title` an beiden Buttons, `disabled` während der Erzeugung.

## 6. Link-Vorschaubild (Open Graph) 1200×630 pro Release

**Problem:** Quadratische Cover wurden von Facebook im 1,91:1-Format oben und unten beschnitten (zusätzlich waren feste 1200×630-Angaben im Layout falsch). **Lösung:** pro Release ein eigenes Bild in genau 1200×630. Quelle: `src/pages/og/[slug].jpg.ts`.

**Aussehen:** Cover quadratisch 630×630 links über die volle Höhe, rechts eine Spalte (Innenabstand 56 px, vertikal zentriert, Abstand 28 px) mit: Artist (Versalien, 20 px, Zeichenabstand 5 px, Akzentfarbe), Titel (fett, Versalien, Schriftgröße nach Länge: bis 14 Zeichen 64 px, bis 28 Zeichen 52 px, sonst 42 px, Zeilenhöhe 1.1), Plattform-Logos (40 px, Abstand 28 px, Akzentfarbe), unten `Jahr · domain`. Hintergrund die Seitenfarbe.

**Technik:**
- `satori` (Layout als Objektbaum, keine JSX nötig) erzeugt SVG, `sharp` macht daraus JPEG (Qualität 88). Satori wandelt Text in Pfade um, zur Laufzeit wird also keine Schrift mehr gebraucht.
- Schriftdaten für Satori müssen `ttf`/`otf`/`woff` sein, **kein woff2**. Die `@fontsource`-Pakete liefern `.woff`. Im Ziel `@fontsource/josefin-sans` und `@fontsource/space-mono` nutzen, die ohnehin installiert sind (`.../files/josefin-sans-latin-<weight>-normal.woff`).
- Cover mit `sharp` auf 630×630 (`fit: cover`) bringen und als Base64-`data:`-URI in `<img>` setzen. Plattform-Logos als Base64-SVG-`data:`-URIs (Farbe ersetzt, `width`/`height` gesetzt).
- Neue Dependencies im Ziel: `satori`. Prüfen, ob `sharp` direkt als Dependency stehen soll.

**Anpassung für SSR:** Die Release-Seite im Ziel ist `prerender = false`. Ein statischer Endpoint mit `getStaticPaths` passt dann nicht. Optionen, die du abwägen sollst:
1. SSR-Endpoint `src/pages/og/[slug].jpg.ts` mit `prerender = false`, Antwort mit `Cache-Control: public, max-age=86400` (oder länger). Prüfen, ob `node_modules/@fontsource/...` im Laufzeit-Image (Dockerfile) vorhanden ist; sonst Schrift beim Build ins Repo legen oder mitkopieren.
2. Bilder beim Build in ein Skript erzeugen und als statische Dateien ablegen.

Variante 1 ist näher an der Quelle, Variante 2 robuster fürs Deployment. Entscheidung begründen.

**`og:image` setzen:** Die Release-Seite zeigt auf `/og/<catalog>.jpg` (absolute URL), `og:image:width=1200`, `og:image:height=630`, `twitter:card=summary_large_image`. Wenn das Layout vorher feste Größenangaben für alle Seiten hat, nur für Seiten mit passendem Bild setzen.

**Nach dem Deploy:** Facebook cached die Vorschau pro URL. Im Sharing Debugger (`developers.facebook.com/tools/debug/`) neu einlesen.

## 7. Strukturierte Daten (JSON-LD)

Im Ziel gibt es noch keine. Auf der Release-Seite ein `MusicAlbum` ausgeben (`<script type="application/ld+json">` mit `JSON.stringify`). Aus der Quelle gelernt:
- `name`: nur der Albumname, **nicht** "Artist - Titel".
- `url`: kanonische URL.
- `byArtist`: ein `MusicGroup` pro Artist; bei mehreren Artists (Trennung an `&` und `,`) ein Array. Im Ziel ist `artist` ein Feld mit Zeichenkette, dort an `&`/`,` splitten, nicht fest "The Moon Records" eintragen.
- `recordLabel`: `{ "@type": "Organization", "name": "The Moon Records" }`.
- `image`, `datePublished` (im Ziel liegt `release_date` vor, dann das volle Datum nehmen), `description` (wenn Text vorhanden), `sameAs` (alle Plattform-URLs).
- Optional: `track` aus `tracks[]`, falls vorhanden.

## 8. Vorherige/nächste Release als echte Links

Im Ziel werden "also on" Releases pro Request zufällig gemischt. Das bleibt, aber zusätzlich am Ende der Seite zwei feste Links, damit Crawler interne Links im HTML sehen und Nutzer chronologisch navigieren können:
- Sortierung stabil nach `release_date` (oder `catalog`), "Previous release" = älteres, "Next release" = neueres. Das erste bzw. letzte Release zeigt nur eine Seite, ein leerer Platzhalter hält das Layout.
- Link zeigt Label (klein, Akzentfarbe, Versalien, Zeichenabstand) und Titel (max. 2 Zeilen).

## 9. Footer neu

Quelle: `src/components/Footer.astro`. Ziel: mobil kompakt und übersichtlich, Socials als Icons in eigener Spalte.

**Mobil (gestapelt):**
1. Marke ("The Moon Records").
2. Social-Icons in einer Reihe, je 44×44 px, links bündig (negativer linker Rand, damit das Symbol optisch an der Textkante sitzt).
3. Links (z. B. Releases, Listen, Impressum, Datenschutz) in einer umbrechenden Reihe, jeder Link mindestens 44 px hoch.
4. Trennlinie, darunter Copyright/Version untereinander.

**Ab md (Desktop):** eine Zeile mit Marke links, Links in der Mitte, Icons rechts als eigene Spalte (Grid `1fr auto auto`, vertikal zentriert), darunter Trennlinie und Credits links/rechts.

**Umsetzung:**
- Reihenfolge nur per `order-*` ändern, damit das DOM sinnvoll bleibt (Marke, Links, Icons).
- Social-Daten als Array `{label, href, icon}` im Frontmatter, per `map` rendern. Welche Socials es gibt, aus den vorhandenen Links ableiten (u. a. Bandcamp aus dem alten Footer). Nichts erfinden.
- Icons: `simple-icons` per Named Imports im Frontmatter (tree-shaken, z. B. `siBandcamp`, `siSpotify`, `siSoundcloud`, `siInstagram`, `siYoutube`) mit `<svg viewBox="0 0 24 24" fill="currentColor"><path d={icon.path}/></svg>`. Alternativ vorhandene `src/assets/dsp/*.svg`. Amazon Music hat Simple Icons nicht mehr. Jede Verlinkung bekommt `aria-label` und `title`, externe Links `target="_blank" rel="noopener noreferrer"`.
- Bestehendes "EST. 2024 · v{pkg.version}" beibehalten.

## 10. Header und mobile Navigation

Quelle: `src/components/Navigation.vue` (Quellrepo), im Ziel `src/components/Header.astro`.

- **Header mobil niedriger:** Quelle `py-5 md:py-10` statt `py-10`. Im Ziel hat der Header `h-16`, dort prüfen, ob er mobil gekürzt werden kann.
- **Mobiles Vollbild-Menü kompakter:** Einträge kleiner (Quelle: `text-xl py-2 tracking-[0.15em]` statt `text-2xl py-3 tracking-widest`), Seitenrand des Panels gleich dem Seitenrand der Seiten.
- **Burger und Schließen-X an derselben Position**, damit beim Öffnen nichts springt. Das X sitzt exakt dort, wo der Burger saß, rechts auf der Seitenrand-Kante.
- **Bündige Kanten:** Header-Logo, Burger, Seiteninhalt (z. B. Back-Link) und Footer haben mobil denselben Seitenrand. In der Quelle ist es überall `1.25rem` (px-5). Im Ziel eine einzige mobile Gutter-Größe wählen und in Header, Seitencontainer (Release-Seite: `px-4 sm:px-6`) und Footer verwenden. Per Messung prüfen, dass `logo.left == back-link.left == 390 - burger.right` gilt.
- **Header-Höhe als CSS-Variable** (`--header-height`, mobil klein, ab md größer), wenn Seiten einen Offset für den fixen Header brauchen.

## 11. Allgemeine Mobile-Regeln (für alle Seiten)

In der Quelle wurde die Startseite von ca. 17.700 px auf ca. 7.100 px Höhe gebracht (390 px Breite). Das Muster, auf andere Seiten übertragen:

- **Abschnittsabstände:** mobil `py-12`, ab md wie bisher (Quelle `py-12 md:py-32`). Überschriften-Abstand unten mobil klein (`mb-6 md:mb-24`).
- **Seitenränder** mobil schmaler und überall gleich (siehe Abschnitt 10).
- **Listen statt großer Karten:** Sekundäre Listen (News, Playlists, weitere Releases) mobil als Zeilen mit kleinem Thumbnail (ca. 5 bis 3,5 rem), Titel und Meta rechts; Beschreibung und "Read more"-Links nur ab md. Die ganze Zeile antippbar (gestreckter Link per `after:absolute after:inset-0`).
- **Covergrids:** mobil zwei Spalten mit kleiner Schrift, Plattform-Icons nur ab md.
- **Lange Fließtexte** mobil einklappen: erster Absatz sichtbar, Rest per "Read more"-Button (JS-Toggle von `data-open` am Elternelement, Absätze `hidden md:block group-data-[open]:block`). Button nur mobil (`md:hidden`), `aria-expanded` pflegen.
- **Embeds** (Player, Videos) mobil schlank, ab md voll.
- **Alles nur mit `md:`-Präfixen ändern**, damit Desktop unverändert bleibt. Prüfen mit 360, 390 und 1440 px Breite: `document.documentElement.scrollWidth - clientWidth == 0`.
- **Touch:** alle Tap-Ziele mindestens 44×44 px, mindestens 8 px Abstand.

## 12. Auto-Bumper für die Version

Quelle: `3e63c76` im Quellrepo (`.husky/pre-commit`, Scripts in `package.json`). Identisch zu tobeworks_8.

- `husky` als Dev-Dependency (`pnpm add -D -E husky`), in `package.json` `"prepare": "husky"`. Danach einmal `pnpm install`, damit `core.hooksPath` gesetzt wird.
- `.husky/pre-commit`:
  ```sh
  npm version patch --no-git-tag-version
  git add package.json
  ```
  (Kein `--no-git-checks`: das ist ein pnpm-Flag, npm warnt nur davor.) Kein `lastchange`-Feld nötig.
- Scripts in `package.json`:
  ```json
  "version:patch": "pnpm version patch --no-git-tag-version",
  "version:minor": "pnpm version minor --no-git-tag-version",
  "version:major": "pnpm version major --no-git-tag-version"
  ```
- Verhalten: Jeder Commit des Nutzers erhöht den Patch (auch Doku und `--amend`). Minor/Major vor dem Commit von Hand erhöhen; der Hook hängt dann noch einen Patch an (mit `HUSKY=0 git commit ...` vermeidbar). Tags setzt der Hook nicht.
- Im Zielrepo gilt weiter: Der Agent committet nicht. Der Hook läuft nur bei Commits des Nutzers. Die aktuelle Version steht `0.3.5`, der Footer zeigt sie schon an.
- Optional (nicht Teil dieser Aufgabe): GitHub-Action für Tags beim Push auf den Hauptbranch.

## 13. Stolperfallen aus der Quelle

- **Globale `p`-Regel überschrieb Tailwind-Abstände.** In der Quelle steht in `global.css` eine ungelayerte Regel `p { margin: 1rem 0; font-weight: 300; ... }`, die gegen Utility-Klassen (in `@layer`) gewinnt. Für kompakte Zeilen daher `div`/`span` statt `p`. Im Ziel prüfen, ob es so eine Regel gibt, bevor `mt-*`/`mb-*` auf `p` verlassen wird.
- **iOS/WebKit-Falle bei Icon-Reihen:** Ein Icon-Feld, dessen Breite nur über `aspect-square` aus der Höhe kommt, mit einem `<svg class="w-full">` darin, bricht in Safari in eine Spalte um (SVG-Standardbreite 300 px zählt als Mindestbreite). Icon-Felder immer mit fester Breite **und** Höhe angeben (`size-4`).
- **Safari und Teilen:** siehe Abschnitt 5 (Bild vor dem Tap erzeugen).
- **SVG ohne `xmlns`** lässt sich nicht als `<img>`/Canvas-Quelle laden.
- **Fonts für Satori:** nur ttf/otf/woff, nicht woff2.
- **Titel splitten** (falls nötig) mit `/\s*-\s+/` statt `/\s+-\s+/`, sonst scheitern Titel wie "A & B- Titel".
- **Facebook-Cache:** Nach Änderungen an `og:image` im Sharing Debugger neu einlesen.
- **Bild-Texte nicht auf "Out now" festlegen** (siehe Abschnitt 5).
- **Texte und Copy** im Zielrepo nach dessen Konventionen schreiben (in der Quelle gilt: keine Gedankenstriche in Site-Texten).

## 14. Abnahme

- [ ] Release-Seite bei 360/390 px: Karte mit Cover und Meta, "Listen on" und "Share" klar getrennt, kein horizontaler Überlauf.
- [ ] Back-Link, Logo und Burger mobil auf einer Kante (Messung).
- [ ] Share: Bild wird als JPEG 1080×1920 erzeugt; auf einem Handy über https öffnet sich das Teilen-Menü; auf Desktop wird die Datei heruntergeladen. Die Bildvorschau mit mindestens zwei Releases (viele Plattformen, langer Titel) geprüft.
- [ ] `/og/<slug>.jpg` liefert ein 1200×630-JPEG; Release-Seite verweist darauf; im Sharing Debugger keine Beschneidung.
- [ ] JSON-LD im Rich-Results-Test oder Schema-Validator ohne Fehler; `byArtist` korrekt bei mehreren Artists.
- [ ] Previous/Next sind echte Links im ausgelieferten HTML.
- [ ] Footer mobil und Desktop wie in Abschnitt 9, alle Tap-Ziele 44 px.
- [ ] Header und Vollbild-Menü mobil kompakter; Desktop unverändert.
- [ ] Bumper: Test-Commit in einem Wegwerf-Repo oder bei dir lokal erhöht die Version um 1 Patch.
- [ ] Der Agent hat nicht gebaut, nicht committet, nicht gepusht und eine Commit-Message im Chat geliefert.

## 15. Referenzdateien im Quellrepo

Alle unter `/Users/tobe/Sites/logic-moon.de/logicmoon_astro/`:

- `src/pages/discography/[slug].astro` (Release-Seite, JSON-LD, Prev/Next, Player-Varianten)
- `src/components/ShareButtons.astro` (Share, Canvas)
- `src/pages/og/[slug].jpg.ts` (Vorschaubild mit satori und sharp)
- `src/platformIcons.ts` (gemeinsame Icon-Liste für Story und OG-Bild)
- `src/components/Footer.astro`, `src/components/Navigation.vue`, `src/styles/global.css` (Header-Höhe)
- Mobile-Muster: `src/components/{About,LatestNews,Playlists,Youtube,LicensingCTA,LabelCTA}.astro`, `src/components/{Discography,DiscographyGrid}.vue`
- `.husky/pre-commit` und `package.json` (Bumper)
