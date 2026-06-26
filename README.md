# Agent Mail Workspace

This workspace records the local Agent Mail CLI setup used for the QQ Agent Mail account.

## Current Setup

- CLI: `agently-cli`
- Package: `@tencent-qqmail/agently-cli`
- Installed version: `1.0.6`
- Installed path: `/opt/homebrew/bin/agently-cli`
- Global skill: `agently-mail`
- Skill path: `/Users/yunaoxiao/.agents/skills/agently-mail`
- Authorized mailbox: `bitdancing@agent.qq.com`

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
