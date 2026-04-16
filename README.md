# The Moon Records — Web

Website for [The Moon Records](https://the-moon-records.de) — an ambient/beatless music label.

Built with Astro, Tailwind CSS v4, and PocketBase.

---

## Stack

- **[Astro](https://astro.build)** v6 — static site with SSR API routes
- **[Tailwind CSS](https://tailwindcss.com)** v4 — utility-first styling
- **[PocketBase](https://pocketbase.io)** — backend for newsletter, promo system, and feedback
- **[Nodemailer](https://nodemailer.com)** — transactional email (double opt-in newsletter)
- **[the-moon-os](https://github.com/Tobeworks/the-moon-os)** — git submodule with release data and shared assets

---

## Local development

### Prerequisites

- Node.js 22+
- pnpm
- [Mailpit](https://mailpit.axllent.org) for local email testing (`brew install mailpit`)

### Setup

```bash
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

---

## Environment variables

See `.env.example` for all required variables.

| Variable | Description |
|----------|-------------|
| `POCKETBASE_URL` | PocketBase instance URL |
| `PUBLIC_SITE_URL` | Public site URL (used in emails) |
| `SMTP_HOST` | SMTP server host |
| `SMTP_PORT` | SMTP port (465 for SSL, 587 for STARTTLS) |
| `SMTP_SECURE` | `true` for SSL, `false` for STARTTLS |
| `SMTP_USER` | SMTP username |
| `SMTP_PASS` | SMTP password |
| `SMTP_FROM` | From address for outgoing mail |

---

## Deployment

Deployed on Kubernetes (Netcup) via ArgoCD. GitHub Actions builds and pushes a Docker image to `ghcr.io/tobeworks/the-moon-web:latest` on every push to `main`. ArgoCD Image Updater handles automatic rollout.

---

## License

Private. All rights reserved.
