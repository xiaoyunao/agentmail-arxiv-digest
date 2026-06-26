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
