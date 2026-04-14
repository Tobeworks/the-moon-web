# Newsletter System — Phantom Grid Web

## Context

Phantom Grid benötigt ein Newsletter-System: Nutzer sollen sich anmelden können (Double Opt-in via E-Mail-Bestätigung), und sich auch wieder abmelden können. Die Subscriber werden in PocketBase gespeichert; E-Mails werden per Nodemailer + SMTP verschickt.

**Repo:** `/Users/tobe/Sites/Phantom Grid/phantom-grid-web`

---

## PocketBase Collection

Collection **`newsletter_subscribers`** muss manuell im PocketBase-Admin angelegt werden:

| Feld | Typ | Optionen |
|---|---|---|
| `email` | Email | required, unique |
| `name` | Text | optional |
| `confirmed` | Bool | default: false |
| `confirmation_token` | Text | — |
| `unsubscribe_token` | Text | — |
| `confirmed_at` | DateTime | optional |
| `confirmation_token_expires_at` | DateTime | optional — Token-Ablauf nach 24h |

API-Rules: alle Regeln auf `""` (nur via Admin-Token / Server-seitig erreichbar, kein öffentlicher Lese-/Schreibzugriff).

---

## Neue Env-Variablen (`.env`)

```
SMTP_HOST=
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=
SMTP_PASS=
SMTP_FROM=newsletter@phantom-grid.de
PUBLIC_SITE_URL=https://phantom-grid.de
PB_ADMIN_EMAIL=
PB_ADMIN_PASSWORD=
```

PocketBase-Schreibzugriff auf die Collection benötigt Admin-Auth (da API-Rules gesperrt sind). Alternativ kann die Collection öffentliche Create-Rechte bekommen, dann braucht man nur für Update/Delete den Admin-Token.

---

## Opt-in Flow

```
1. POST /api/newsletter/subscribe
   → Subscriber anlegen (confirmed=false, confirmation_token zufällig)
   → Confirmation E-Mail senden: /newsletter/confirm?token=...

2. GET /api/newsletter/confirm?token=...
   → confirmed=true setzen, confirmed_at setzen, confirmation_token leeren
   → Welcome-E-Mail mit Unsubscribe-Link senden
   → Redirect → /newsletter/confirmed

3. GET /api/newsletter/unsubscribe?token=...
   → Subscriber löschen
   → Redirect → /newsletter/unsubscribed
```

---

## Dateien

### Neues Package
```
pnpm add nodemailer
pnpm add -D @types/nodemailer
```

### Modify: `src/lib/pocketbase.ts`
Neue Funktionen hinzufügen:
- `createSubscriber(email, name)` — erstellt unconfirmed Subscriber, gibt Record zurück
- `confirmSubscriber(token)` — setzt confirmed=true per token, gibt Record zurück
- `unsubscribeByToken(token)` — löscht Subscriber per unsubscribe_token

Verwendet Admin-Auth-Header für alle Newsletter-API-Calls (PB Admin token via env).

### Neu: `src/lib/mailer.ts`
Nodemailer-Instanz + zwei Export-Funktionen:
- `sendConfirmationEmail(to, name, confirmToken)` — HTML-Template mit Bestätigungs-Link
- `sendWelcomeEmail(to, name, unsubscribeToken)` — HTML-Template mit Unsubscribe-Link

E-Mail-Templates im Phantom Grid Stil (dark background, accent red, monospace font).

### Neu: `src/pages/api/newsletter/subscribe.ts` (POST)
1. Pflichtfeld: `email`, optional: `name`
2. E-Mail-Format validieren (Regex, vor PB-Call)
3. **Immer `{ ok: true }` zurückgeben** — keine E-Mail-Enumeration möglich
4. Duplicate-Check: falls schon vorhanden und confirmed → "bereits angemeldet"-Mail; falls unconfirmed → neue Confirmation-Mail senden
5. `createSubscriber()` aufrufen (mit `confirmation_token_expires_at = now + 24h`)
6. `sendConfirmationEmail()` aufrufen

### Neu: `src/pages/api/newsletter/confirm.ts` (GET)
1. `token` Query-Parameter auslesen
2. `confirmSubscriber(token)` aufrufen — prüft auch ob `confirmation_token_expires_at` noch gültig
3. `sendWelcomeEmail()` aufrufen
4. `Redirect → /newsletter/confirmed` (bei abgelaufenem Token: `/newsletter?expired=1`)

### Neu: `src/pages/api/newsletter/unsubscribe.ts` (GET)
1. `token` Query-Parameter auslesen
2. `unsubscribeByToken(token)` aufrufen
3. `Redirect → /newsletter/unsubscribed`

### Neu: `src/components/NewsletterForm.astro`
Wiederverwendbares Formular-Component:
- Felder: E-Mail (required), Name (optional)
- Submit via `fetch` (kein Page-Reload)
- Zustände: idle / loading / success / error
- Styling: passt zum bestehenden Design (dark surface, accent-red Button, monospace)

### Neu: `src/pages/newsletter/index.astro`
- Standalone-Seite mit `NewsletterForm` eingebettet
- Kurze Beschreibung was der Newsletter ist

### Neu: `src/pages/newsletter/confirmed.astro`
- Bestätigungs-Erfolgsmeldung ("Du bist jetzt angemeldet!")

### Neu: `src/pages/newsletter/unsubscribed.astro`
- Abmelde-Bestätigung ("Du wurdest erfolgreich abgemeldet.")

---

## Kritische Dateien

- `src/lib/pocketbase.ts` — bestehende Muster werden übernommen (fetch-basiert, kein SDK)
- `src/pages/api/promo/feedback.ts` — API-Route-Muster (prerender=false, JSON-Antworten)
- `src/styles/global.css` — Design-Tokens (accent, surfaces, inputs, buttons)

---

## Sicherheitshinweise

- **Tokens**: `crypto.randomBytes(32).toString('hex')` → 64 hex-Chars, 256-bit Entropie, keine Sonderzeichen → keine PocketBase-Filter-Injection möglich
- **E-Mail-Enumeration**: Subscribe gibt immer `{ ok: true }`, Info-Mail geht an bestehende E-Mail
- **Token-Ablauf**: Confirmation-Token nach 24h ungültig
- **Kein öffentlicher PB-Zugriff**: API-Rules gesperrt, Zugriff nur via Server-seitigem Admin-Token
- **Rate Limiting**: Empfehlung — via nginx `limit_req_zone` für `/api/newsletter/subscribe`

## Verifikation

1. `pnpm dev` starten
2. `/newsletter` aufrufen → Formular sichtbar
3. Gültige E-Mail eintragen → API antwortet `{ ok: true }`, Confirmation-Mail kommt an
4. Link in Mail anklicken → `/newsletter/confirmed` erscheint, Welcome-Mail kommt
5. Unsubscribe-Link in Welcome-Mail anklicken → `/newsletter/unsubscribed`, Datensatz weg
6. PocketBase Admin prüfen: Collection hat den Subscriber nach Schritt 3 (unconfirmed), nach Schritt 4 (confirmed), nach Schritt 5 (gelöscht)
