# dailyarxiv

`dailyarxiv` is an email subscription service for personalized arXiv astro-ph digests.

Subscribers do not install anything. They send one subscription email, then receive focused daily summaries when relevant astro-ph papers appear.

## Subscribe

Send an email from the address where you want to receive the digest.

```text
To: dailyarxiv@agent.qq.com
Subject: Subscribe to dailyarxiv

dark matter; little red dot; stellar streams; dwarf galaxies
```

## Email Format

- The subject must be exactly `Subscribe to dailyarxiv`.
- The body is a list of interests separated by semicolons.
- Interests can be research directions, keywords, fixed objects, surveys, methods, or author names.
- The sender address is used as the delivery address.
- Sending a new subscription email from the same address updates the profile.

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

On arXiv astro-ph mailing days, `dailyarxiv` reads the daily arXiv email and selects papers matching each subscriber's interests. The summary is written in Chinese by default and follows a stable research-note structure:

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
- follow-up questions

The goal is not to translate abstracts mechanically. The service first uses the subscriber profile to recall candidate papers, then uses Codex to judge semantic relevance and produce a more useful research summary.

## Schedule

arXiv astro-ph daily emails usually arrive Monday-Friday, Beijing time, between 09:00 and 11:00.

`dailyarxiv` checks at:

- 12:00 Beijing time for subscription requests and the main daily arXiv run
- 14:00 Beijing time for one fallback check if no daily email was processed at noon

If arXiv does not send an astro-ph daily email that day, the service stops for that day.

## Status

This is an early private service. The current backend is built around:

- `dailyarxiv@agent.qq.com` for inbound subscription and arXiv daily mail
- Codex for semantic triage and summaries
- SMTP for automatic outgoing receipts and digests

Operational notes for maintainers live in [`docs/OPERATIONS.md`](docs/OPERATIONS.md). Architecture notes live in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Contact

To subscribe or update your interests, email:

```text
dailyarxiv@agent.qq.com
```
