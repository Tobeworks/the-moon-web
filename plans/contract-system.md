# Artist Contract System

Automatische Vertragsverwaltung für Solo-Releases — Verträge zwischen The Moon Records
und einem einzelnen Artist, ohne Split-Beteiligung.

**Status:** Designdokument. Nicht implementiert. Kein Termin.

---

## Context

Das [Split-Sheet-System](../../the-moon-web/src/pages/split-sheet/) löst die
Rechteklärung zwischen mehreren Beteiligten an einem Release: jeder Mitwirkende bestätigt
elektronisch seinen Prozentanteil. Es setzt voraus, dass es überhaupt eine *Aufteilung*
gibt.

Ein wachsender Teil des Katalogs sind aber Solo-Releases — ein einzelner Artist, keine
Kollaboration, kein Split. Für die braucht es trotzdem eine dokumentierte, elektronisch
signierte Zustimmung zu den Bedingungen, unter denen The Moon Records das Release
veröffentlicht: Vertriebsrechte, Laufzeit, Beteiligung, Exklusivität — was bisher, genau
wie die Split Sheets früher, als Word-Dokument von Hand verschickt und unterschrieben
wurde.

Die Idee: dasselbe Grundmuster wie beim Split-Sheet-System — individueller Signing-Link,
elektronische Signatur mit Zeitstempel/IP/Hash als Nachweis, PocketBase als Speicher,
Astro-Routen fürs Signieren — für einen strukturell anderen Fall: **ein** Vertragspartner
auf Artist-Seite statt mehrerer, und ein echter Vertragstext statt einer Prozentzahl.

Dieses Dokument beschreibt, was dabei wiederverwendet werden kann, wo sich die beiden
Systeme unterscheiden müssen, und welche Entscheidungen noch offen sind, bevor das gebaut
wird.

**Betroffenes Repo:** `the-moon-web` (Astro + PocketBase + Vue-Admin), analog zum
Split-Sheet-System. Referenzimplementierung dort: `src/pages/split-sheet/`,
`src/pages/api/split-sheet/`, `src/pages/api/admin/split-sheets/`,
`src/admin/modules/splitsheets/`, `src/lib/pocketbase.ts`, `src/lib/mailer.ts`.

---

## Was vom Split-Sheet-System übernommen wird

Das Split-Sheet-System hat mehrere Entscheidungen bereits getroffen, die sich 1:1
übertragen lassen — hier nicht neu erfinden:

| Baustein | Fundstelle im Split-Sheet-System | Übertragbar? |
|---|---|---|
| Signing-Token | `generateSigningToken()` in `splitSheetHash.ts`, `crypto.randomBytes(24).toString('hex')` | Ja, unverändert |
| Dokument-Hash | `hashDocument()`, SHA-256 über kanonisches JSON des zum Signaturzeitpunkt gezeigten Inhalts | Ja, als Konzept — Inhalt ändert sich (siehe unten) |
| IP-Erfassung | `x-forwarded-for` / `x-real-ip`-Fallback, Muster aus `api/promo/download.ts` | Ja, unverändert |
| PocketBase-Sicherheitsmodell | Alle Regeln `""` (offen) statt `null` — PocketBase ist nicht öffentlich erreichbar, das ist die eigentliche Grenze, nicht die PB-Regel. Kein Superuser-Token im Code. | Ja, unverändert — siehe `AGENTS.md` Abschnitt 5 "Fallstricke" |
| Mailer-Pattern | `sendXxxEmail(to, name, ..., url)` in `src/lib/mailer.ts`, `baseHtml()`-Wrapper, `escapeHtml()` für Nutzereingaben | Ja, neue Funktion `sendContractSigningEmail(...)` nach demselben Muster |
| Löschschutz für Signiertes | Route prüft `signed_at` vor jedem `DELETE`, lehnt mit `409` ab | Ja, unverändert |
| `.env`/Dev-Fallstrick | `PUBLIC_SITE_URL` ist in `.env` fest auf Produktion gesetzt; `import.meta.env.DEV` muss explizit geprüft werden, sonst zeigen lokal erzeugte Links immer auf die Live-Domain | Ja, unverändert — derselbe Bug wäre sonst erneut fällig |
| Fehlerbehandlung | Nie ein roher 500er — jede Route fängt DB-Fehler ab und übersetzt sie in eine lesbare Meldung (z. B. Unique-Constraint-Verletzung → 409 mit Klartext) | Ja, unverändert |
| Admin-Formular-Muster | Release-Dropdown aus `the-moon-os/data/releases.json`, Autofill wo möglich (siehe `applyReleaseDefaults()` in `SplitSheetsIndex.vue`) | Ja, für die Release-Zuordnung |

---

## Wo es sich unterscheidet

### 1. Ein Unterzeichner statt mehrerer

Ein Split hat `artist_name` + `percentage` + `role` — mehrere Zeilen pro Release. Ein
Vertrag hat **genau eine** Gegenpartei: den Artist. Kein Formular mit "+ Add Split", kein
Summen-Check auf 100%. Stattdessen: Release (oder Artist, siehe offene Frage 1) wählen,
Artist-Kontakt eintragen, Vertrag erzeugen.

### 2. Es gibt echten Vertragstext, nicht nur eine Zahl

Ein Split Sheet zeigt strukturierte Daten (Name, Prozent, Rolle) in einer Tabelle. Ein
Vertrag ist ein **Fließtext mit echten Bedingungen** — Vertriebsrechte, Laufzeit,
Kündigungsfristen, Beteiligung. Das braucht ein neues Konzept, das es bei Splits nicht
gab: **Vertragsvorlagen** mit Platzhaltern, die pro Vertrag befüllt werden.

Beispiel einer Vorlage (Markdown, ähnlich wie `about.md` für Releases):

```markdown
# Release Agreement

Between **The Moon Records** ("Label") and **{{artist_name}}** ("Artist"),
regarding the release **{{release_title}}** ({{catalog}}).

## 1. Grant of Rights
The Artist grants the Label exclusive worldwide distribution rights for the
Release across all digital platforms for a term of {{term_months}} months
from the release date ({{release_date}}).

## 2. Royalties
The Label shall pay the Artist {{royalty_rate}}% of net revenue...

## 3. Term & Termination
...
```

Gerendert wird das genauso wie in `CampaignEditor.vue` bereits vorhanden: `marked` ist
schon Dependency, das dortige Markdown-Editor-mit-Live-Preview-Muster (Split-Screen
Textarea + `v-html="renderedHtml"`) lässt sich für den Template-Editor direkt
übernehmen.

### 3. Snapshot-Pflicht — der wichtigste Unterschied

Beim Split Sheet reicht ein **Hash** über den Inhalt: Prozentzahlen ändern sich selten,
und falls doch, ist der Hash Beleg genug, dass sich etwas geändert hat. Bei einem
mehrseitigen Vertragstext reicht das nicht — wenn sich die Vorlage später ändert (neue
Klausel, andere Standardkonditionen), muss der **tatsächliche Wortlaut**, den der Artist
gesehen und unterschrieben hat, wortwörtlich abrufbar bleiben. Ein Hash beweist nur, dass
sich etwas geändert hat, nicht *was* unterschrieben wurde.

Deshalb: beim Erzeugen eines Vertrags wird der **vollständig gerenderte Text** (Platzhalter
bereits ersetzt) als eigenes Feld gespeichert (`rendered_body`), nicht nur ein Verweis auf
die Vorlage. Der Hash wird zusätzlich weiterhin über genau diesen gespeicherten Text
gebildet — Snapshot und Hash ergänzen sich, sie ersetzen sich nicht.

### 4. Öffentliche Sichtbarkeit ist fraglich

Der öffentliche Split-Sheet-Link (`/split-sheet/{slug}`) existiert, weil er **an
Distributoren** geht — als Nachweis, dass alle Rechteinhaber zugestimmt haben. Ein
Vertrag zwischen Label und Artist hat vermutlich keinen vergleichbaren Dritten, dem er
gezeigt werden muss — im Gegenteil, die Konditionen (Royalty-Rate, Laufzeit) sind eher
vertraulich. Ob es überhaupt eine öffentliche Statusseite braucht, ist offen (siehe unten).

---

## Vorgeschlagenes Datenmodell

Zwei PocketBase-Collections, in Anlehnung an `split_sheet_releases` + `splits`:

### `contract_templates`

| Feld | Typ | Hinweis |
|---|---|---|
| `name` | text | z. B. "Standard Release Agreement v1" |
| `body_md` | text | Markdown mit `{{platzhaltern}}` |
| `is_active` | bool | genau eine Vorlage ist Standard bei Neuanlage |

`listRule`/`viewRule`/`createRule`/`updateRule`: `""` (offen, Netzwerkisolation als
Grenze — siehe oben). `deleteRule: ""`, aber serverseitig blockiert, sobald ein Vertrag
diese Vorlage referenziert (analog zum Signiert-Schutz bei Splits).

### `contracts`

| Feld | Typ | Hinweis |
|---|---|---|
| `template` | relation → `contract_templates` | welche Vorlage verwendet wurde |
| `catalog` | text | Release-Referenz in `releases.json`, optional (siehe offene Frage 1) |
| `artist_name` | text | |
| `artist_email` | email, optional | fehlt sie → kein Automailversand, Link manuell verschicken (identisch zum Split-Sheet-Verhalten) |
| `public_slug` | text, unique | falls öffentliche Seite gebraucht wird (offene Frage 2) |
| `rendered_body` | text | **der vollständige, zum Signaturzeitpunkt gezeigte Text** — siehe Abschnitt "Snapshot-Pflicht" |
| `signing_token` | text, unique | wie bei Splits |
| `status` | text | `draft` \| `signed` |
| `signed_name` | text, optional | |
| `signed_at` | date, optional | |
| `ip_address` | text, optional | |
| `document_hash` | text, optional | SHA-256 über `rendered_body` |
| `token_expires_at` | date, optional | |

Kein separates `signatures`-Objekt nötig — wie beim Split-Sheet-System werden die
Signaturfelder direkt auf den Datensatz gelegt, da 1:1-Beziehung (ein Vertrag, ein
Unterzeichner).

---

## Routen (gespiegelt an die Split-Sheet-Pfade)

| Route | Zweck |
|---|---|
| `GET /contract/{slug}` *(falls gebraucht — offene Frage 2)* | Öffentliche Read-Only-Statusseite |
| `GET /contract/sign/{token}` | Zeigt `rendered_body` gerendert, Namensfeld, Bestätigen-Button — analog `split-sheet/sign/[token].astro` |
| `POST /api/contract/sign` | `{token, signed_name}` — Token-Prüfung, Ablauf-Prüfung, Signieren, `409` bei Doppelsignatur |
| `GET/POST /api/admin/contracts` | Liste + Neuanlage (Vorlage wählen, Platzhalter befüllen, `rendered_body` erzeugen, Mail verschicken) |
| `DELETE /api/admin/contracts/[id]` | Nur wenn `signed_at` leer — sonst `409` |
| `POST /api/admin/contracts/[id]/resend` | Signing-Link erneut verschicken oder Link zum manuellen Versand liefern |
| `GET/POST/PATCH/DELETE /api/admin/contract-templates` | Vorlagen-CRUD |

---

## Admin-UI

Neues Modul `src/admin/modules/contracts/ContractsIndex.vue`, strukturell wie
`SplitSheetsIndex.vue`: Formular für neuen Vertrag (Release-Dropdown mit Autofill,
Artist-Kontakt, Vorlagen-Auswahl, Platzhalter-Felder je nach gewählter Vorlage) + Liste
bestehender Verträge mit Status, Resend/Delete-Aktionen.

Zusätzlich ein Vorlagen-Tab (Muster: Promo-Admin mit "Promo List" / "Promo Records" oder
Newsletter-Admin mit "Campaigns" / "Subscribers" — zwei Tabs in einer Seite statt zwei
Menüpunkten), der den Markdown-Editor mit Live-Preview aus `CampaignEditor.vue`
wiederverwendet.

Navigation: neuer Eintrag im Sidebar-Array in `src/admin/App.vue`, neue Route in
`src/admin/router.ts`, neue Dashboard-Kachel in `Dashboard.vue` — alle drei nach
demselben Muster wie beim Split-Sheet-Rollout.

---

## Sicherheits- und Nachweisüberlegungen

Strenger als bei Splits, weil es hier um echte Vertragsbedingungen statt einer
Prozentzahl geht:

- **Snapshot statt nur Hash** — siehe oben, das ist die zentrale Abweichung.
- **Placeholder-Vollständigkeit prüfen** — vor dem Erzeugen sicherstellen, dass alle
  `{{platzhalter}}` der gewählten Vorlage tatsächlich einen Wert bekommen haben; ein
  unaufgelöster Platzhalter im unterschriebenen Text wäre ein handfester Fehler, keine
  Kleinigkeit.
- **Bestätigungshürde vor dem Signieren?** — der Split-Sheet-Signierflow braucht nur
  einen eingetippten Namen. Für einen mehrseitigen Vertrag könnte ein "Scroll to
  bottom, bevor der Button aktiv wird"-Mechanismus oder eine explizite Checkbox ("Ich
  habe den Vertrag gelesen und stimme zu") angemessener sein — offene Frage 4.
- Rechtlicher Hinweis unverändert vom Split-Sheet-System übernehmen: einfache
  elektronische Signatur, keine qualifizierte — das gilt hier genauso, sollte aber bei
  echten Vertragsbedingungen noch deutlicher kommuniziert werden als bei einer
  Prozent-Bestätigung.

---

## Offene Design-Fragen

Bewusst nicht vorentschieden — vor dem Bau zu klären:

1. **Vertrag pro Release oder pro Artist?** Ein einzelner Vertrag könnte alle künftigen
   Releases eines Artists abdecken (dauerhafte Zusammenarbeit) statt pro Release neu
   unterschrieben zu werden. Ändert das Datenmodell (`catalog` würde optional/entfallen,
   dafür bräuchte es eine Artist-Entity — die es aktuell nirgends im System gibt, auch
   nicht bei Splits, wo Artist-Name/E-Mail nur lose Felder sind).
2. **Braucht es überhaupt eine öffentliche Statusseite?** Bei Splits ja (Nachweis für
   Distributoren). Bei einem Label-Artist-Vertrag ist unklar, wer diese Seite je
   aufrufen würde — falls nicht, entfällt `public_slug` und die gesamte
   `/contract/{slug}`-Route ersatzlos.
3. **Eine feste Vorlage zum Start oder von Anfang an mehrere Vertragstypen?** Falls nur
   ein Vertragstyp aktuell existiert, ließe sich der Template-Editor fürs erste
   weglassen und der Text fest im Code hinterlegen — deutlich weniger Aufwand, aber
   dann nicht mehr "so einfach wie möglich" im Sinne von Anpassbarkeit ohne Deploy.
4. **Zusätzliche Bestätigungshürde vor dem Signieren?** Siehe Abschnitt oben.
5. **Reicht die einfache elektronische Signatur weiterhin,** oder braucht es für echte
   Verträge (im Gegensatz zu einer Split-Prozentzahl) eine höhere Stufe (z. B.
   qualifizierte elektronische Signatur über einen Drittanbieter)? Das wäre eine
   grundsätzlich andere technische Route (externe Signatur-API statt Eigenbau) und
   sollte früh entschieden werden, nicht nachträglich draufgesetzt.

---

## Nicht-Ziele für eine erste Version

Analog zu den Nicht-Zielen des Split-Sheet-Systems:

- Automatisierter PDF-Export
- Zahlungs-/Royalty-Auszahlungslogik (nur der Vertragstext, keine Abrechnung)
- Verhandlungs-/Redlining-Workflow — die erste Version ist take-it-or-leave-it wie bei
  den Splits, kein Hin-und-Her am Dokument
- Mehrsprachigkeit des Vertragstexts
- Automatische Versionsverwaltung/Diff-Ansicht zwischen Vorlagen-Versionen — falls
  Vorlagen mehrfach geändert werden, reicht fürs Erste "eine Vorlage ist aktiv", keine
  Versionshistorie mit Vergleichsansicht
