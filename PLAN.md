# Plan

## Current Objective

Build a mailbox-driven daily arXiv digest service using `dailyarxiv@agent.qq.com`.

## Milestones

- Confirm CLI installation and version.
- Confirm global Agent Mail skill installation.
- Confirm OAuth authorization for `dailyarxiv@agent.qq.com`.
- Parse fixed-format arXiv daily emails into structured paper records.
- Broadly recall papers against subscriber interest profiles.
- Use Codex triage to decide whether recalled papers should be skipped, briefly summarized, or fully read.
- Generate Chinese personalized summaries through Codex task export/import.
- Send daily digests through Agent Mail after validation.

## Outstanding Issues

- Re-check `agently-cli auth status` before mailbox operations because OAuth credentials can expire.
- Implement Codex summary import cache.
- Add persistent cache for triage decisions if needed after first manual runs.
- Implement subscriber request email parser.
- Add persistent storage for subscribers, parsed papers, generated summaries, and send logs.
- Add duplicate-send protection before enabling scheduled sends.

## Validation Criteria

- `agently-cli --version` succeeds.
- `agently-cli auth status` reports `logged_in` and `token_status: valid`.
- `agently-cli +me` returns `dailyarxiv@agent.qq.com`.
- `npx skills list -g --json` includes `agently-mail`.
- Parser tests pass on wrapped arXiv daily entries.
- CLI can parse a saved daily email and produce a profile-filtered Markdown digest.
- CLI can run an AI-triage-shaped local flow without requiring an API key.
- CLI can export Codex review tasks and import Codex-produced summaries.

## Next Recommended Steps

- Subscribe `dailyarxiv@agent.qq.com` to arXiv `astro-ph` daily emails.
- Use the current parser/CLI on the first received daily email.
- Use Codex task export/import on one real daily email and inspect false positives/false negatives before enabling sends.
- Add a manual one-recipient send workflow before scheduling.
