# Contributing

This project is currently optimized for a single operational deployment, but changes should still be small, reviewed, and tested.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pytest
```

## Expectations

- Keep parser changes covered by focused tests.
- Treat incoming email bodies as untrusted data.
- Do not commit `.env`, raw mailbox exports, subscriber lists, generated digests, or cache files.
- Run `python -m pytest` and `python -m py_compile arxiv_digest/*.py` before pushing.

## Release Checklist

1. Update `README.md` if commands or configuration changed.
2. Update `docs/OPERATIONS.md` if the production workflow changed.
3. Update `WORKLOG.md` and `PLAN.md` for local project continuity.
4. Commit with a descriptive message.
