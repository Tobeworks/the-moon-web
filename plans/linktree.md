# Linktree

Konfigurierbare Bio-Link-Seite (`/links`) für Social-Profile — Mix aus eigenen
Release-Karten und frei verwaltbaren Links, über den bestehenden Web-Admin gepflegt.
Zusatzfeature: dieselbe Release-Karte hebt auf der Startseite das neueste Release hervor.

**Status:** Designdokument, freigegeben. Bereit für Implementierungsplan.

**Betroffenes Repo:** `the-moon-web` (Astro + PocketBase + Vue-Admin). Referenz für
das Admin-Muster: `src/admin/modules/contracts/`, `src/pages/api/admin/contract-templates/`,
`src/lib/pocketbase.ts`. Referenz für die Release-Darstellung: `src/pages/releases/[slug].astro`
(Mobile-Block), `src/components/DspLinks.astro`, `src/components/AudioPlayer.astro`.

---

## Context

Zwei Bedürfnisse, ein wiederverwendbarer Baustein:

1. Eine klassische Linktree-artige Seite für die Bio-Links der Social-Profile (Instagram
   etc.) — Mix aus Releases (Dropdown-Auswahl aus dem Katalog) und frei eingetragenen
   Links zu anderen Systemen (Newsletter, Bandcamp, Kontakt …).
2. Auf der Startseite soll das neueste Release nicht nur Teil des gleichförmigen
   Release-Grids sein, sondern sichtbar herausgestellt werden.

Beide Anzeigen brauchen dieselbe kompakte Darstellung eines einzelnen Release: Cover,
Titel/Artist, echte klickbare DSP-Links, optional den Player — so dimensioniert, dass
Cover + Titel + DSP-Links auch auf einem Handy-Bildschirm ohne Scrollen sichtbar sind.
Genau dieses Layout existiert bereits als Mobile-Block auf der Release-Detailseite
(`[slug].astro`, `max-w-[min(100%,38vh)]`-Cover + `DspLinks` + `AudioPlayer`). Statt es
zweimal neu zu bauen, wird es einmal als eigene Komponente extrahiert.

**Sicherheitsmodell:** PocketBase ist Cluster-intern, nicht öffentlich erreichbar — Astro
ist die eigentliche Grenze (siehe `AGENTS.md` Abschnitt 5, bestätigt in
`12_create_contracts.js`). Die neue Collection folgt demselben Muster: alle Rules `""`,
kein Superuser-Token im Code, Schreibzugriff ausschließlich über die authentifizierten
`/api/admin/*`-Routen (Cookie-Check in `src/middleware.ts`).

---

## 1. Geteilte Komponente: `ReleaseSpotlight.astro`

Neue Komponente unter `src/components/ReleaseSpotlight.astro`, Props: `{ release }`
(ein Eintrag aus `releases.json`). Rendert:

- Cover, viewport-begrenzt (`max-w-[min(100%,38vh)]`-Muster aus `[slug].astro`)
- Badges: Catalog, Format, Genre
- Titel (`h2`, nicht `h1` — Seiten mit dieser Komponente haben ihre eigene Überschrift),
  Artist
- `DspLinks` (echte Links, `visiblePlatforms` nur wenn `release_date` in der
  Vergangenheit liegt — Logik 1:1 aus `[slug].astro` übernommen)
- `AudioPlayer`, wenn released; sonst derselbe `TRANSMISSION_PENDING`-Block wie auf der
  Release-Seite
- Cover verlinkt zusätzlich auf `/releases/{catalog}`, `target="_blank"` — die Karte ist
  **kein** großer `<a>`-Wrapper, weil `DspLinks` und `AudioPlayer` selbst interaktive
  Elemente/Links enthalten (verschachtelte Anchors sind ungültig — siehe Kommentar in
  `DspLinks.astro` zum `static`-Prop)

Wird von den beiden folgenden Punkten konsumiert. `[slug].astro` selbst wird **nicht**
angefasst — der dortige Mobile-Block bleibt unverändert, um eine bereits funktionierende
Seite nicht anzufassen; die neue Komponente ist eine parallele, für die neuen Stellen
zugeschnittene Extraktion desselben Musters.

---

## 2. Linktree — Datenmodell

Neue PocketBase-Collection `linktree_items` (Migration in
`tools/pocketbase/pb_migrations/`, nächste freie Nummer):

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `type` | select `release` \| `link` | ja | Eintragsart |
| `position` | number | ja | Sortierreihenfolge, aufsteigend |
| `release_catalog` | text | nur bei `type=release` | z. B. `TMR-015`, Referenz in `releases.json`, nicht dupliziert |
| `label` | text | nur bei `type=link` | Button-Text |
| `url` | text | nur bei `type=link` | Ziel-URL |

Rules: `listRule`/`viewRule`/`createRule`/`updateRule`/`deleteRule` alle `""` (siehe
Sicherheitsmodell oben — analog zu `contracts`/`split_sheet_releases`).

`getLinktreeItems()` etc. ergänzen `src/lib/pocketbase.ts` nach demselben Muster wie
`getContractTemplates()` (`fetch` gegen `PB_URL`, `sort=position` als Query-Param).

---

## 3. Linktree — Admin

Neues Modul `src/admin/modules/linktree/LinktreeIndex.vue`, Route `/linktree` in
`src/admin/router.ts` + Eintrag in der Admin-Navigation (wo immer die bestehenden
Modul-Links stehen, analog zu `contracts`/`split-sheets`).

- Formular „Neuer Eintrag": Typ-Umschalter → entweder Release-Dropdown (Katalog aus
  `the-moon-os/data/releases.json`, Muster aus `ContractsIndex.vue`s
  `<select v-model="form.catalog">`) oder Label+URL-Felder
- Liste bestehender Einträge, sortiert nach `position`: kompakte Zeile (Release:
  Catalog/Artist/Titel; Link: Label + URL) mit ▲/▼-Buttons (am Rand deaktiviert) und
  Löschen — kein Enable/Disable-Flag, ein Eintrag existiert oder nicht
- Klick auf eine Zeile lädt sie zum Bearbeiten ins Formular (wie der
  Template-Editor in `ContractsIndex.vue`)

API-Routen unter `src/pages/api/admin/linktree/`, Stil identisch zu
`contract-templates/index.ts`:

- `index.ts` — `GET` (Liste), `POST` (neuer Eintrag, `position` = aktuelles Maximum + 1)
- `[id].ts` — `PATCH` (Bearbeiten), `DELETE`
- `reorder.ts` — `POST { id, direction: 'up' | 'down' }`: lädt die sortierte Liste,
  tauscht `position` mit dem Nachbarn, zwei `PATCH`-Aufrufe. Serverseitig, damit der
  Client keine rohen `position`-Werte schreibt.

---

## 4. Linktree — öffentliche Seite

Neue Seite `src/pages/links.astro`, Route `/links`, `prerender = false` (SSR, damit
Admin-Änderungen sofort sichtbar sind — wie die anderen dynamischen Seiten).

- Lädt `getLinktreeItems()`, sortiert nach `position`
- `type=link`: eigener, mono/uppercase gerahmter Button-Stil (passend zum bestehenden
  Terminal-Look), `target="_blank" rel="noopener noreferrer"`
- `type=release`: sucht den Release in `releases.json` per `release_catalog`
  (case-insensitive, wie das Slug-Matching in `[slug].astro`); fehlt er (z. B. Release
  wurde aus dem Katalog entfernt), wird der Eintrag **stillschweigend übersprungen**,
  nicht als Fehler angezeigt — Konvention wie an anderen Stellen im Codebase, die auf
  `releases.json` verweisen. Rendert `<ReleaseSpotlight release={found} />`.
- Layout: einfache vertikale Liste innerhalb von `BaseLayout` (Header/Footer wie überall)

---

## 5. Zusatzfeature — Startseiten-Spotlight

`src/pages/index.astro` bekommt eine neue Sektion zwischen Hero und Release-Grid:

```
// LATEST TRANSMISSION
<ReleaseSpotlight release={latestRelease} />
```

`latestRelease` wird über das bereits vorhandene `latestCatalog` in `index.astro`
aufgelöst (String-Sort über `catalog`, z. B. `TMR-001` → `TMR-015` — dieselbe Konvention,
die `ReleaseList.astro` für die Grid-Sortierung schon verwendet; **nicht** über
`release_date`, um konsistent mit dem Rest der Seite zu bleiben).

Ist das neueste Release noch nicht erschienen (`release_date` in der Zukunft), zeigt die
Komponente automatisch den `TRANSMISSION_PENDING`-Zustand statt Player/DSP-Links — das
ist Verhalten der Komponente selbst, keine Sonderlogik auf der Startseite.

`index.astro` wird **nicht** sonst umgebaut — nur die neue Sektion wird eingefügt.

---

## Offene Punkte

Keine — alle Entscheidungen (Route, Reorder-UI, kein Enable-Flag, Player-Umfang,
geteilte Komponente, Sortierkonvention für „neuestes Release") wurden im Vorgespräch
festgelegt.
