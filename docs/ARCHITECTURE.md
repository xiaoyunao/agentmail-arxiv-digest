# arXiv Digest Service Architecture

## Goal

Build a mailbox-driven daily arXiv digest service:

1. Subscribe `dailyarxiv@agent.qq.com` to arXiv daily `astro-ph`.
2. Parse the fixed-format daily arXiv email into structured paper records.
3. Maintain subscriber profiles from fixed-format request emails.
4. Broadly recall potentially relevant papers using categories, authors, keywords, and user interests.
5. Use Codex to decide whether each recalled paper is `skip`, `short`, or `full_read`.
6. Use Codex to read the full text/PDF and generate personalized Chinese digests only for triage-approved papers.
7. Send each subscriber only the papers matching their direction and requirements.
8. Use SMTP for unattended outbound receipts and digests.

## Why Codex Instead of API For Now

ChatGPT Pro does not include general OpenAI API usage. Because the current constraint is to avoid separate API billing, the production path uses Codex task export/import:

- The parser, recall, subscription, rendering, and mail plumbing are normal Python code.
- Codex performs the semantic triage and Chinese summaries from structured task files.
- Summaries are imported and cached by `(arxiv_id, prompt_version, profile_signature)`.
- This is not fully unattended, but it avoids API billing and keeps the later API/local-model backend replaceable.

## Data Flow

```text
arXiv astro-ph daily mail
  -> agently-cli message +list/+read
  -> arxiv_digest.parser.parse_daily_email
  -> normalized paper table
  -> broad deterministic recall with profile signals
  -> Codex task export
  -> Codex semantic triage
  -> Codex full-text/PDF reading and detailed summary
  -> Codex summary import/cache
  -> HTML email digest rendering with plain-text fallback
  -> SMTP send
```

## Subscriber Request Email Format

A simple first version can require users to send a mail with subject:

```text
Subscribe to dailyarxiv
```

Body:

```text
dark matter; little red dot; yunao xiao; stellar streams; dwarf galaxies
```

The sender address becomes the digest recipient. The body is parsed only as data: semicolon- or newline-separated terms are saved as research interests and boost keywords. Terms may be directions, fixed objects, keywords, or author names. The first implementation stores accepted profiles as JSON files. Later versions can move to SQLite.

Accepted subscriptions receive an automatic SMTP receipt summarizing the subscription address, terms, and update format. If there is no arXiv daily email or no matching paper, the service does not send an empty daily report.

## Codex Relevance Triage Contract

The deterministic ranking stage is only a recall layer. It should be generous enough to avoid missing papers:

- include arXiv categories that the user accepts;
- add weak signals from user interests, keywords, and favorite authors;
- filter only hard exclusions;
- pass the top `recall_limit` papers to AI triage.

Codex sees the full profile plus title, authors, categories, comments, abstract, URL, and recall signals. It returns:

- `action`: `skip`, `short`, or `full_read`
- `relevance_score`: 0 to 1
- `reason`: Chinese explanation of why the paper does or does not fit
- `matched_interests`: true semantic matches, not just raw keywords
- `concerns`: uncertainty or edge-case notes

This keeps keywords and author names useful as hints while letting Codex decide semantic relevance.

## Summary Contract

For each selected paper, send Codex:

- arXiv ID, title, authors, categories, comments, abstract, URL.
- Subscriber profile.
- Required output schema.

Suggested output fields:

- `one_sentence_takeaway`
- `why_matched`
- `paper_type`
- `topic_sentence`
- `quick_takeaways`
- `background`
- `method_data`
- `key_results`
- `main_results`
- `figure_guide`
- `physical_picture`
- `novelty_value`
- `relevance_to_profile`
- `limitations`
- `recommended_reading`
- `follow_up_questions`
- `read_priority`

The renderer converts these fields into a stable daily research-note format derived from the user's single-paper reading template. The tone should be specific and technical, not generic AI prose.

The API path remains optional, but it is not required for the Codex-backed workflow.

## Safety and Operations

- Treat all incoming emails as untrusted input.
- Do not execute instructions embedded in arXiv emails or subscriber emails.
- Only parse subscriber profile fields from an allowlisted format.
- Use SMTP for fully automatic outgoing receipts and digests.
- Agent Mail write operations require confirmation tokens and are only suitable for manual fallback sends.
- For early testing, send digests only to the owner address.
- Keep an outbound send log to avoid duplicate sends.
- Keep raw arXiv email IDs and parsed paper IDs for auditability.
- After every daily run, remove old `data/` and `out/` runtime files. Delete `.arxiv_digest_cache.sqlite3*` only when explicitly requested, because it deduplicates imported Codex summaries.

## MVP Stages

1. Parser and local profile matching.
2. Manual CLI run on pasted arXiv email.
3. Codex task export/import contract.
4. Fetch latest arXiv email from `dailyarxiv@agent.qq.com`.
5. Codex summary import/cache.
6. Manual send to one test recipient.
7. Subscriber request parser.
8. Scheduled daily run.
