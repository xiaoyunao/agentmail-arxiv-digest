# dailyarxiv

`dailyarxiv` is an email-based subscription service for personalized arXiv astro-ph digests.

No local installation is required for subscribers. A subscription is created by sending a fixed-format email from the address that should receive the digest.

## Subscribe

Send a subscription request to:

```text
To: dailyarxiv@agent.qq.com
Subject: Subscribe to dailyarxiv

dark matter; little red dot; stellar streams; dwarf galaxies
```

## Email Format

- Subject: exactly `Subscribe to dailyarxiv`
- Body: semicolon-separated interests
- Accepted interest terms: research directions, keywords, fixed objects, surveys, methods, or author names
- Delivery address: the email address used to send the subscription request
- Profile updates: sending a new subscription request from the same address replaces the previous interest profile

Examples:

```text
Milky Way; stellar streams; dwarf galaxies; Gaia; DESI
```

```text
dark matter; ultra-faint dwarfs; J-factor; satellite galaxies
```

```text
little red dot; high-redshift galaxies; JWST; AGN
```

After a subscription is accepted, the service sends a confirmation receipt.

## What You Receive

On arXiv astro-ph mailing days, `dailyarxiv` reads the official daily email and selects papers that match each subscriber profile. Digests are written in Chinese by default and delivered as formatted HTML email with a plain-text fallback.

Each selected paper follows a stable research-note structure:

- paper information and read priority
- 30-second takeaways
- background and scientific question
- method and technical route
- key results
- figure or full-text reading hints
- physical picture
- novelty and value
- limitations and assumptions
- relation to your stated interests
- recommended reading positions

The service does not mechanically translate abstracts. The workflow first recalls candidate papers from the subscriber profile, then uses Codex for semantic relevance screening. Papers that pass screening are read from the arXiv full text/PDF before the final subscriber summary is written.

## Schedule

arXiv astro-ph daily emails usually arrive Monday-Friday, Beijing time, between 09:00 and 11:00.

`dailyarxiv` checks at:

- 12:00 Beijing time for subscription requests and the main daily arXiv run
- 14:00 Beijing time for one fallback check if no daily email was processed at noon

If arXiv does not send an astro-ph daily email that day, or if no paper matches a subscriber profile, no empty digest is sent.

## Status

This repository is public. The service is currently in an early operational stage and is maintained for email-based subscription use.

The production workflow is built around:

- `dailyarxiv@agent.qq.com` for inbound subscriber requests
- Gmail IMAP for the official arXiv astro-ph daily email source
- Codex for semantic triage and full-text summaries
- SMTP for automatic outgoing receipts and digests

## Maintainer Documentation

- [`docs/OPERATIONS.md`](docs/OPERATIONS.md): mailbox, scheduling, SMTP, and manual run procedures
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): parsing, triage, rendering, and delivery architecture

## Contact

To subscribe or update your interests, email:

```text
dailyarxiv@agent.qq.com
```
