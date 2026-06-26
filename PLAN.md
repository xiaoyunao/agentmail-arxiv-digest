# Plan

## Current Objective

Build a mailbox-driven daily arXiv digest service using `dailyarxiv@agent.qq.com`.

## Milestones

- Confirm CLI installation and version.
- Confirm global Agent Mail skill installation.
- Confirm OAuth authorization for `dailyarxiv@agent.qq.com`.
- Parse fixed-format arXiv daily emails into structured paper records.
- Match papers against subscriber interest profiles.
- Generate Chinese personalized summaries through GPT API calls.
- Send daily digests through Agent Mail after validation.

## Outstanding Issues

- Re-check `agently-cli auth status` before mailbox operations because OAuth credentials can expire.
- Implement GPT API summarization and cache.
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

## Next Recommended Steps

- Subscribe `dailyarxiv@agent.qq.com` to arXiv `astro-ph` daily emails.
- Use the current parser/CLI on the first received daily email.
- Add OpenAI API summarization with schema validation and caching.
- Add a manual one-recipient send workflow before scheduling.
