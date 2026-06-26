# Operations

## Mailboxes

- Inbound mailbox: `dailyarxiv@agent.qq.com`
- arXiv subscription source: `astro-ph@arxiv.org`
- Subscriber request subject: `Subscribe to dailyarxiv`

Agent Mail is used for reading inbound messages. Automatic outbound mail should use SMTP because Agent Mail write operations require an explicit confirmation token.

## Automatic Send Backend

Create a local `.env` from `.env.example` and fill the SMTP variables:

```bash
cp .env.example .env
chmod 600 .env
```

Required variables:

- `DAILYARXIV_SMTP_HOST`
- `DAILYARXIV_SMTP_USERNAME`
- `DAILYARXIV_SMTP_PASSWORD`

Common optional variables:

- `DAILYARXIV_SMTP_PORT`
- `DAILYARXIV_SMTP_SECURITY`: `starttls`, `ssl`, or `none`
- `DAILYARXIV_SMTP_FROM_EMAIL`
- `DAILYARXIV_SMTP_FROM_NAME`

## Subscriber Import

Users subscribe by sending an email from the address that should receive the digest.

```text
Subject: Subscribe to dailyarxiv

dark matter; little red dot; stellar streams; dwarf galaxies
```

Import new subscriptions and send automatic receipts:

```bash
python -m arxiv_digest.mail_cli import-subscriptions --send-receipts
```

Profiles are stored under `subscribers/`, which is ignored by git.

## Daily Timing

arXiv astro-ph daily usually arrives Monday-Friday Beijing time between 09:00 and 11:00.

- 12:00 Asia/Shanghai: main processing run.
- 14:00 Asia/Shanghai: fallback check only if the noon run did not process today's email.
- If no daily email exists by 14:00, stop for the day.

## Manual Commands

Fetch the latest daily email:

```bash
python -m arxiv_digest.mail_cli latest-arxiv --output data/latest-astro-ph.txt
```

Export tasks for Codex review:

```bash
python -m arxiv_digest.cli \
  --mail-file data/latest-astro-ph.txt \
  --profile profiles.galactic.example.json \
  --triage codex \
  --export-codex-tasks codex_tasks.json \
  --output out/recalled.md
```

Import Codex summaries and render a digest:

```bash
python -m arxiv_digest.cli \
  --mail-file data/latest-astro-ph.txt \
  --profile profiles.galactic.example.json \
  --triage codex \
  --import-codex-summaries codex_summaries.json \
  --output out/digest.md
```

Send a digest automatically through SMTP:

```bash
python -m arxiv_digest.mail_cli send-smtp \
  --to user@example.com \
  --subject "dailyarxiv astro-ph digest" \
  --body-file out/digest.md
```

`send-smtp` records successful sends in `.arxiv_digest_send_log.sqlite3` and skips duplicate sends with the same recipient, subject, and body. Pass `--force` only when a duplicate send is intentional.

Clean old runtime files:

```bash
python -m arxiv_digest.mail_cli cleanup --keep-days 7
```

Do not use `--drop-cache` in normal daily operation; the sqlite cache prevents repeat summary imports.
