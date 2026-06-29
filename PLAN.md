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
- Generate Chinese personalized summaries through Codex task export/import after full-text/PDF reading.
- Render each selected paper with a stable HTML email research-note digest template and a plain-text fallback.
- Import fixed-format subscription requests with subject `Subscribe to dailyarxiv` and semicolon-separated body terms.
- Send subscription receipts automatically through SMTP.
- Send daily digests automatically through SMTP.
- Remove old runtime files after daily sends.
- Keep Agent Mail send as a manual fallback only.

## Outstanding Issues

- Re-check `agently-cli auth status` before mailbox operations because OAuth credentials can expire.
- Codex cron automations can fail before command execution when the selected model is at capacity; check `automation_runs` and Codex logs after scheduled windows.
- Confirm the arXiv astro-ph subscription is actually delivering directly to `dailyarxiv@agent.qq.com`; as of 2026-06-29 12:43 CST, the inbox still only had the 2026-06-26 forwarded astro-ph test message.
- Add persistent cache for triage decisions if needed after first manual runs.
- Add persistent storage for parsed papers and generated summaries.
- Decide whether daily cleanup should drop summary cache or keep it for deduplication.

## Validation Criteria

- `agently-cli --version` succeeds.
- `agently-cli auth status` reports `logged_in` and `token_status: valid`.
- `agently-cli +me` returns `dailyarxiv@agent.qq.com`.
- `npx skills list -g --json` includes `agently-mail`.
- Parser tests pass on wrapped arXiv daily entries.
- Parser accepts forwarded rich-text arXiv daily messages with `<br>` and `&nbsp;` markup.
- CLI can parse a saved daily email and produce profile-filtered text and HTML digests.
- `latest-arxiv --local-date "$(date +%F)"` refuses older arXiv daily messages instead of saving them as today's run.
- CLI can run an AI-triage-shaped local flow without requiring an API key.
- CLI can export Codex review tasks and import Codex-produced summaries.
- Subscription import accepts `Subscribe to dailyarxiv` emails and ignores other subjects.
- Subscription import strips rich-text HTML from Gmail-style bodies.
- Subscription import can send confirmation receipts with `--send-receipts`.
- Final digest uses the stable formatted daily research-note template and does not include a follow-up-questions section.
- Digest emails can be sent without Agent Mail confirmation through `send-smtp`.
- Cleanup command removes old runtime files and only drops cache with an explicit flag.
- Gmail SMTP smoke test succeeds for automatic outgoing mail.
- Outbound SMTP sends are recorded in `.arxiv_digest_send_log.sqlite3` and duplicate sends are skipped by dedupe key.

## Next Recommended Steps

- Subscribe `dailyarxiv@agent.qq.com` to arXiv `astro-ph` daily emails.
- Use the current parser/CLI on the first received daily email.
- Use Codex task export/import on one real daily email and inspect false positives/false negatives before enabling sends.
- Run one full end-to-end daily digest on a real astro-ph daily email.
- Add parsed-paper/run-state persistence if daily operational logs show it is needed.
