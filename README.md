# The Moon Records — Web

Website for [The Moon Records](https://the-moon-records.de) — an independent ambient/beatless music label.

Built with Astro, Tailwind CSS v4, Vue 3, and PocketBase.

---

## Stack

- **[Astro](https://astro.build)** v6 — hybrid SSR with `@astrojs/node` adapter
- **[Tailwind CSS](https://tailwindcss.com)** v4 — utility-first styling via `@tailwindcss/vite`
- **[Vue 3](https://vuejs.org)** + **[Pinia](https://pinia.vuejs.org)** + **[Vue Router](https://router.vuejs.org)** — admin SPA
- **[PocketBase](https://pocketbase.io)** v0.36 — self-hosted backend (newsletter, promo system, feedback, campaigns, promo list)
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
| Admin dashboard | http://localhost:4321/admin |

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

### Promo list

A contact list for bloggers, journalists, DJs etc. who want to receive new releases. No double opt-in.

- Sign up at `/promo-list`
- Welcome email sent immediately on signup
- Unsubscribe via link in welcome email → `/api/promo-list/unsubscribe?token=...`
- Admin manages the list at `/admin/promo`

**PocketBase collection:** `promo_subscribers`
Fields: `email`, `name`, `unsubscribe_token`

#### Sending a promo to the list

1. Go to `/admin/promo` → click **Send Promo**
2. Select a release from the dropdown (populated from `releases.json`)
3. Optionally set an expiry date for the promo links
4. **Send Test** — sends a real promo email to a single address so you can verify the link and layout before the full send
5. **Send to all** — generates an individual `promos` record (with a unique token) for every subscriber and sends the promo email

Each subscriber gets a personal link (`/promo/[token]`) — download stats are tracked per token in the `download_events` collection. The send result shows how many succeeded and how many failed.

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

Campaign sending is managed at `/admin/newsletter` (login required).

**Flow:**
1. Login at `/admin/login` with your PocketBase user credentials
2. Create a new campaign (subject + HTML body via Markdown)
3. Edit and preview the campaign
4. Send a test email to yourself
5. Click Send — emails go to all confirmed subscribers
6. Campaign is marked `sent` with sent/failed counts

**PocketBase collection:** `campaigns`
Fields: `subject`, `body_html`, `body_md`, `body_text`, `status` (draft/sending/sent), `sent_at`, `sent_count`, `failed_count`

All emails use the branded HTML template in `src/lib/mailer.ts` and include an unsubscribe link.

---

## Admin dashboard

The admin area is a Vue 3 SPA mounted at `/admin` via an Astro catch-all route.

**Authentication:** Login at `/admin/login` with a PocketBase `users` collection account. The JWT token is stored in an httpOnly cookie (`admin_token`) and validated on every request via the Astro middleware.

**Modules:**
- `/admin` — Dashboard
- `/admin/newsletter` — Campaign list, create, edit, send
- `/admin/promo` — Promo list subscriber management

**Stack:** Vue Router (`createWebHistory('/admin')`), Pinia, same Tailwind tokens as the public site.

---

## PocketBase collections

| Collection | Purpose |
|-----------|---------|
| `promos` | Promo links per release/recipient |
| `feedback` | Reviews submitted via promo pages |
| `download_events` | Download tracking (promo, quality, timestamp) |
| `newsletter_subscribers` | Double opt-in subscriber list |
| `campaigns` | Newsletter campaign drafts + send history |
| `promo_subscribers` | Promo list contacts (no opt-in required) |

> **Note on collection access rules:** `promos`, `newsletter_subscribers`, `promo_subscribers`, and `campaigns` have open create/list rules (`""`). This is safe because PocketBase is not exposed externally — all writes go through Astro API routes which are protected by the admin middleware.

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

> **Note:** Admin authentication uses PocketBase `users` collection — no `ADMIN_PASSWORD` env var needed.

---

## Project structure

```
src/
  admin/              # Vue 3 SPA (admin dashboard)
    modules/
      newsletter/     # Campaign list + editor
      promo/          # Promo list management
    App.vue           # Sidebar layout
    router.ts         # Vue Router config
    main.ts           # SPA entry point
  components/         # Astro components (AudioPlayer, NewsletterForm, ReleaseCard, …)
  layouts/            # BaseLayout
  lib/
    admin-api.ts      # Admin API client (campaigns, promo subscribers)
    mailer.ts         # Nodemailer transporter + all email templates
    pocketbase.ts     # PocketBase REST API helpers
  middleware.ts       # Admin route protection (token validation)
  pages/
    admin/
      login.astro     # Login page
      [...path].astro # Vue SPA catch-all
    api/
      admin/          # Protected admin API routes
        login.ts      # Auth (sets httpOnly cookie)
        logout.ts
        newsletter/   # Campaigns CRUD, send, test
        promo-list/   # Promo subscriber CRUD + send.ts + test.ts
      newsletter/     # Public API (subscribe, confirm, unsubscribe)
      promo/          # Promo API (download, feedback)
      promo-list/     # Public API (subscribe, unsubscribe)
    newsletter/       # Public newsletter pages
    promo/            # Promo pages
    promo-list/       # Promo list signup + unsubscribed confirmation
    releases/         # Release detail pages
  styles/
    global.css        # Tailwind v4 theme tokens + base styles
the-moon-os/          # Git submodule — release data + shared assets
tools/
  pocketbase/
    pb_migrations/    # PocketBase schema migrations (run on startup)
```

---

## Deployment

Deployed on Kubernetes (Netcup) via ArgoCD. Two separate deployments:

- **the-moon-web** — the Astro app (`ghcr.io/tobeworks/the-moon-web:latest`)
- **the-moon-pocketbase** — PocketBase with persistent volume (`ghcr.io/tobeworks/the-moon-pocketbase:latest`)

GitHub Actions builds and pushes images on every push to `main`. ArgoCD Image Updater watches both images and handles automatic rollout. Config lives in the `netcup` ArgoCD repo under `apps/the-moon-web/` and `apps/the-moon-pocketbase/`.

PocketBase is accessible externally at `pb.the-moon-records.de` (for admin access).

---

## License

Private. All rights reserved.
