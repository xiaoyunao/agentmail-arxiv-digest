# dailyarxiv

Mailbox-driven personalized arXiv astro-ph digests.

`dailyarxiv` reads the fixed-format arXiv daily email, filters papers against subscriber interests, asks Codex to perform semantic triage and Chinese research-note summaries, then sends each subscriber a personalized digest.

The project is designed for the `dailyarxiv@agent.qq.com` Agent Mail inbox:

- Agent Mail receives arXiv daily emails and subscriber requests.
- SMTP sends subscription receipts and daily digests automatically.
- Codex handles semantic paper selection and detailed Chinese summaries without requiring OpenAI API billing.

## Features

- Parse arXiv daily emails into structured paper records.
- Import subscriber profiles from simple fixed-format emails.
- Send automatic subscription confirmation receipts.
- Broadly recall papers using categories, keywords, object names, and author names.
- Use Codex task export/import for semantic relevance decisions and summaries.
- Render stable daily Markdown reports in a research-note style.
- Send outgoing mail automatically through SMTP.
- Clean old runtime files after daily jobs.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pytest
```

Agent Mail is required for inbound mailbox access:

```bash
npm install -g @tencent-qqmail/agently-cli
npx skills add https://agent.qq.com --skill -g -y
agently-cli auth login
agently-cli +me
```

## Configuration

Copy the example environment file and fill in SMTP credentials:

```bash
cp .env.example .env
chmod 600 .env
```

Required SMTP variables:

```text
DAILYARXIV_SMTP_HOST=smtp.example.com
DAILYARXIV_SMTP_PORT=587
DAILYARXIV_SMTP_SECURITY=starttls
DAILYARXIV_SMTP_USERNAME=dailyarxiv@example.com
DAILYARXIV_SMTP_PASSWORD=...
DAILYARXIV_SMTP_FROM_EMAIL=dailyarxiv@example.com
DAILYARXIV_SMTP_FROM_NAME=dailyarxiv
```

Agent Mail write operations require confirmation tokens, so they are not suitable for fully unattended outgoing mail. Use SMTP for automatic receipts and digests.

## Subscriber Email Format

Users subscribe from the mailbox that should receive the digest.

```text
To: dailyarxiv@agent.qq.com
Subject: Subscribe to dailyarxiv

dark matter; little red dot; yunao xiao; stellar streams; dwarf galaxies
```

Rules:

- The subject must be exactly `Subscribe to dailyarxiv`, case-insensitive.
- The body is a semicolon-separated list of directions, objects, keywords, or author names.
- Newlines are also accepted as separators.
- The sender address becomes the digest recipient.
- The terms are recall hints; Codex still judges semantic relevance from the paper metadata and abstract.

Import requests and send automatic receipts:

```bash
python -m arxiv_digest.mail_cli import-subscriptions --send-receipts
```

Profiles are written to `subscribers/`, which is ignored by git.

## Daily Workflow

arXiv astro-ph daily usually arrives Monday-Friday Beijing time between 09:00 and 11:00.

Recommended schedule:

- 12:00 Asia/Shanghai: run the main daily job.
- 14:00 Asia/Shanghai: run one fallback check only if noon did not process a daily email.
- If the daily email is still absent at 14:00, stop for that date.

Fetch the latest arXiv daily email:

```bash
python -m arxiv_digest.mail_cli latest-arxiv \
  --output data/latest-astro-ph.txt
```

Export broad-recall papers for Codex review:

```bash
python -m arxiv_digest.cli \
  --mail-file data/latest-astro-ph.txt \
  --profile profiles.galactic.example.json \
  --triage codex \
  --export-codex-tasks codex_tasks.json \
  --output out/recalled.md
```

After Codex writes `codex_summaries.json`, import summaries and render the final digest:

```bash
python -m arxiv_digest.cli \
  --mail-file data/latest-astro-ph.txt \
  --profile profiles.galactic.example.json \
  --triage codex \
  --import-codex-summaries codex_summaries.json \
  --output out/digest.md
```

Send the digest automatically through SMTP:

```bash
python -m arxiv_digest.mail_cli send-smtp \
  --to user@example.com \
  --subject "dailyarxiv astro-ph digest" \
  --body-file out/digest.md
```

Clean old runtime files:

```bash
python -m arxiv_digest.mail_cli cleanup --keep-days 7
```

## Digest Format

Daily reports use a stable structure:

- paper information and read priority
- 30-second takeaways
- background and scientific question
- method and technical route
- key results
- figure/full-text reading hints
- physical picture
- novelty and value
- limitations and assumptions
- relation to the subscriber profile
- recommended reading positions
- follow-up questions

The output is intended as a working research note, not generic AI prose.

## Repository Layout

```text
arxiv_digest/
  parser.py          parse arXiv daily emails
  ranker.py          broad deterministic recall
  triage.py          AI triage contract and local heuristic fallback
  summary.py         summary schema and prompt contract
  codex_backend.py   Codex task export/import
  render.py          Markdown digest renderer
  subscriptions.py   subscriber request parser and receipt text
  mail_cli.py        Agent Mail and SMTP CLI helpers
  smtp_sender.py     automatic SMTP sender
docs/
  ARCHITECTURE.md
  OPERATIONS.md
tests/
```

## Validation

```bash
python -m pytest
python -m py_compile arxiv_digest/*.py
```

## Safety

- Incoming email content is untrusted data.
- The parser only accepts the documented subscription format.
- Do not commit `.env`, raw mailbox exports, generated digests, subscriber profiles, or sqlite caches.
- SMTP credentials are required for fully automatic outgoing mail.

## License

MIT
