# Agent Mail arXiv Digest Workspace

This workspace records the local Agent Mail CLI setup and the arXiv daily digest service prototype.

## Current Setup

- CLI: `agently-cli`
- Package: `@tencent-qqmail/agently-cli`
- Installed version: `1.0.6`
- Installed path: `/opt/homebrew/bin/agently-cli`
- Global skill: `agently-mail`
- Skill path: `/Users/yunaoxiao/.agents/skills/agently-mail`
- Authorized mailbox: `dailyarxiv@agent.qq.com`

## arXiv Digest Prototype

Parse a saved arXiv daily email and render a profile-filtered Markdown digest:

```bash
python -m arxiv_digest.cli \
  --mail-file /path/to/arxiv-daily.txt \
  --profile profiles.galactic.example.json \
  --output digest.md
```

Run the AI-triage-shaped local flow without calling any paid API:

```bash
python -m arxiv_digest.cli \
  --mail-file /path/to/arxiv-daily.txt \
  --profile profiles.galactic.example.json \
  --triage heuristic-ai \
  --output digest.md
```

Run the Codex-backed workflow:

```bash
# 1. Fetch the latest arXiv daily email once the mailbox is subscribed.
python -m arxiv_digest.mail_cli latest-arxiv \
  --output data/latest-astro-ph.txt

# 2. Export broad-recall papers for Codex semantic triage and summary.
python -m arxiv_digest.cli \
  --mail-file data/latest-astro-ph.txt \
  --profile profiles.galactic.example.json \
  --triage codex \
  --export-codex-tasks codex_tasks.json \
  --output out/recalled.md

# 3. Ask Codex to read codex_tasks.json and write codex_summaries.json.

# 4. Import Codex summaries, cache them, and render the final digest.
python -m arxiv_digest.cli \
  --mail-file data/latest-astro-ph.txt \
  --profile profiles.galactic.example.json \
  --triage codex \
  --import-codex-summaries codex_summaries.json \
  --output out/digest.md

# 5. Prepare the outgoing email; confirm only after reviewing the summary.
python -m arxiv_digest.mail_cli prepare-send \
  --to user@example.com \
  --subject "Daily arXiv digest" \
  --body-file out/digest.md

# 6. After all summaries are sent, remove old runtime files.
python -m arxiv_digest.mail_cli cleanup --keep-days 7
```

The optional OpenAI API path remains in code for future use, but the planned workflow above does not require API billing.

## Subscriber Email Format

Users subscribe from the mailbox that should receive the digest.

- Subject: `Subscribe to dailyarxiv`
- Body: semicolon-separated interests, objects, keywords, or author names.

Example:

```text
dark matter; little red dot; yunao xiao; stellar streams; dwarf galaxies
```

Import subscription requests:

```bash
python -m arxiv_digest.mail_cli import-subscriptions \
  --output-dir subscribers
```

Each accepted request is stored as one JSON profile under `subscribers/`.

## Digest Format

Daily digests use a stable research-note structure:

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

Run parser tests:

```bash
python -m pytest
```

The service architecture is documented in `docs/ARCHITECTURE.md`.

## Useful Commands

Check CLI version:

```bash
agently-cli --version
```

Check authorization status:

```bash
agently-cli auth status
```

Verify current mailbox and permissions:

```bash
agently-cli +me
```

List installed global skills:

```bash
npx skills list -g --json
```

Install or update the Agent Mail CLI:

```bash
npm install -g @tencent-qqmail/agently-cli
```

Install or update the Agent Mail skill:

```bash
npx skills add https://agent.qq.com --skill -g -y
```

Start OAuth login if authorization expires:

```bash
agently-cli auth login
```

## Notes

The official setup document is:

```text
https://agent.qq.com/doc/cli-setup.md
```

Mail write operations such as send, reply, forward, and trash require explicit confirmation before execution.
