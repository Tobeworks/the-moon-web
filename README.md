# The Moon Records — Web

Website for [The Moon Records](https://the-moon-records.de) — an independent ambient/beatless music label.

Built with Astro, Tailwind CSS v4, and PocketBase.

---

## Stack

- **[Astro](https://astro.build)** v6 — static site with SSR API routes
- **[Tailwind CSS](https://tailwindcss.com)** v4 — utility-first styling via `@tailwindcss/vite`
- **[PocketBase](https://pocketbase.io)** v0.36 — self-hosted backend (newsletter, promo system, feedback, campaigns)
- **[Nodemailer](https://nodemailer.com)** — transactional email
- **[the-moon-os](https://github.com/Tobeworks/the-moon-os)** — git submodule containing release data (`data/releases.json`) and shared assets

---

## Local development

### Prerequisites

- Node.js 22+
- pnpm
- [Mailpit](https://mailpit.axllent.org) for local email testing (`brew install mailpit`)

### Setup

```bash
# Clone with submodule
git clone --recurse-submodules <repo-url>

# Install dependencies
pnpm install

# Download PocketBase binary
pnpm setup:pb

# Copy env file and fill in values
cp .env.example .env
```

### Run

```bash
# Start everything: PocketBase + Mailpit + Astro dev server
pnpm start
```

| Service | URL |
|---------|-----|
| Website | http://localhost:4321 |
| PocketBase admin | http://localhost:8090/_/ |
| Mailpit (email preview) | http://localhost:8025 |
| Newsletter admin | http://localhost:4321/admin/newsletter |

---

## Features

### Release pages

Releases are stored in `the-moon-os/data/releases.json` (git submodule). Each release has a dedicated page at `/releases/[catalog-slug]` with:

- Artwork, metadata, platform links
- Embedded audio player (`src/components/AudioPlayer.astro`)
- Public feedback/reviews from the promo system
- Streaming is blocked until `release_date` is reached

### Promo system

Journalists and listeners receive a unique promo link: `/promo/[token]`

- Token is stored in PocketBase `promos` collection with `release_slug`, `recipient_name`, `recipient_email`, expiry
- Promo page shows the release with a download button (128kbps / 320kbps zip) and a feedback form
- Feedback (name, comment, optional URL) is stored in PocketBase `feedback` collection
- Confirmed feedback appears publicly on the release page under `// TRANSMISSIONS_RECEIVED`
- Reviewer can optionally provide a website URL which gets linked next to their name

**Creating a promo:** manually via PocketBase admin at `http://localhost:8090/_/` — create a record in the `promos` collection with the recipient details and the release slug.

**Download endpoint:** `src/pages/api/promo/download.ts` — validates token, builds zip from track URLs, streams to browser.

### Newsletter (double opt-in)

Subscribers sign up at `/newsletter` or via the form on the homepage.

**Flow:**
1. User submits email (+ optional name)
2. Confirmation email sent via Nodemailer
3. User clicks confirm link → `/api/newsletter/confirm?token=...`
4. Welcome email sent, subscriber marked confirmed in PocketBase
5. Unsubscribe via link in every email → `/api/newsletter/unsubscribe?token=...`

**PocketBase collection:** `newsletter_subscribers`
Fields: `email`, `name`, `confirmed`, `confirmation_token`, `confirmation_token_expires_at`, `unsubscribe_token`, `confirmed_at`

**Pages:** `/newsletter`, `/newsletter/confirmed`, `/newsletter/unsubscribed`

### Newsletter campaigns (admin)

Campaign sending is managed at `/admin/newsletter` (password protected via `ADMIN_PASSWORD` env var).

**Flow:**
1. Login at `/admin/login`
2. Create a new campaign (subject + HTML body + optional plain text)
3. Edit and preview the campaign
4. Click Send — emails go to all confirmed subscribers
5. Campaign is marked `sent` with sent/failed counts

**PocketBase collection:** `campaigns`
Fields: `subject`, `body_html`, `body_text`, `status` (draft/sending/sent), `sent_at`, `sent_count`, `failed_count`

All emails use the branded HTML template in `src/lib/mailer.ts` and include an unsubscribe link.

---

## PocketBase collections

| Collection | Purpose |
|-----------|---------|
| `promos` | Promo links per release/recipient |
| `feedback` | Reviews submitted via promo pages |
| `download_events` | Download tracking (promo quality + timestamp) |
| `newsletter_subscribers` | Opt-in subscriber list |
| `campaigns` | Newsletter campaign drafts + send history |

Migrations live in `tools/pocketbase/pb_migrations/` and run automatically on PocketBase startup.

---

## Environment variables

See `.env.example` for all required variables.

| Variable | Description |
|----------|-------------|
| `POCKETBASE_URL` | PocketBase instance URL (default: `http://pocketbase:8090` in prod) |
| `PUBLIC_SITE_URL` | Public site URL — used in confirmation and campaign emails |
| `SMTP_HOST` | SMTP server host |
| `SMTP_PORT` | SMTP port (`465` for SSL, `587` for STARTTLS) |
| `SMTP_SECURE` | `true` for SSL, `false` for STARTTLS |
| `SMTP_USER` | SMTP username |
| `SMTP_PASS` | SMTP password |
| `SMTP_FROM` | From address for outgoing mail |
| `ADMIN_PASSWORD` | Password for `/admin` area |

---

## Project structure

```
src/
  components/       # Astro components (AudioPlayer, NewsletterForm, ReleaseCard, …)
  layouts/          # BaseLayout
  lib/
    mailer.ts       # Nodemailer transporter + all email templates
    pocketbase.ts   # PocketBase REST API helpers (promos, feedback, newsletter, campaigns)
  pages/
    admin/          # Password-protected admin UI
      login.astro
      newsletter/   # Campaign list, new, edit
    api/
      admin/        # Admin API routes (login, logout, campaigns CRUD, send)
      newsletter/   # Public API (subscribe, confirm, unsubscribe)
      promo/        # Promo API (download, feedback)
    newsletter/     # Public newsletter pages
    promo/          # Promo pages
    releases/       # Release detail pages
  styles/
    global.css      # Tailwind v4 theme tokens + base styles
the-moon-os/        # Git submodule — release data + shared assets
tools/
  pocketbase/
    pb_migrations/  # PocketBase schema migrations (run on startup)
```

---

## Deployment

Deployed on Kubernetes (Netcup) via ArgoCD. Two separate deployments:

- **the-moon-web** — the Astro app (`ghcr.io/tobeworks/the-moon-web:latest`)
- **the-moon-pocketbase** — PocketBase with persistent volume (`ghcr.io/tobeworks/the-moon-pocketbase:latest`)

GitHub Actions builds and pushes images on every push to `main`. ArgoCD Image Updater handles automatic rollout. Config lives in the `netcup` ArgoCD repo under `apps/the-moon-web/` and `apps/the-moon-pocketbase/`.

PocketBase is accessible externally at `pb.the-moon-records.de` (for admin access).

---

## License

Private. All rights reserved.
