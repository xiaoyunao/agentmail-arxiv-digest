# Plan

## Current Objective

Maintain a small local workspace for QQ Agent Mail CLI setup notes and future Agent Mail tasks.

## Milestones

- Confirm CLI installation and version.
- Confirm global Agent Mail skill installation.
- Confirm OAuth authorization for `bitdancing@agent.qq.com`.
- Record setup and recovery commands in project documentation.

## Outstanding Issues

- Re-check `agently-cli auth status` before future mailbox operations because OAuth credentials can expire.
- If authorization is expired, run `agently-cli auth login` and complete the browser OAuth flow.

## Validation Criteria

- `agently-cli --version` succeeds.
- `agently-cli auth status` reports `logged_in` and `token_status: valid`.
- `agently-cli +me` returns `bitdancing@agent.qq.com`.
- `npx skills list -g --json` includes `agently-mail`.

## Next Recommended Steps

- For read-only mailbox work, use `agently-cli message +list`, `message +search`, or `message +read`.
- For write operations, request and wait for explicit user confirmation before sending, replying, forwarding, or trashing mail.
