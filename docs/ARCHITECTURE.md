# arXiv Digest Service Architecture

## Goal

Build a mailbox-driven daily arXiv digest service:

1. Subscribe `dailyarxiv@agent.qq.com` to arXiv daily `astro-ph`.
2. Parse the fixed-format daily arXiv email into structured paper records.
3. Maintain subscriber profiles from fixed-format request emails.
4. Generate personalized Chinese digests with GPT API calls.
5. Send each subscriber only the papers matching their direction and requirements.

## Why GPT API Instead of Codex

Codex should be used for development and operations. The production summarizer should call the OpenAI API directly because:

- API usage can be metered, logged, cached, retried, and rate-limited independently.
- The summarization prompt can be versioned in the repository.
- Each paper summary can be cached by `(arxiv_id, prompt_version, profile_signature)`.
- The service can run unattended from cron, a server, or GitHub Actions without consuming Codex interactive quota.

## Data Flow

```text
arXiv astro-ph daily mail
  -> agently-cli message +list/+read
  -> arxiv_digest.parser.parse_daily_email
  -> normalized paper table
  -> subscriber profile matching
  -> GPT API summary generation
  -> Markdown/HTML digest rendering
  -> agently-cli message +send
```

## Subscriber Request Email Format

A simple first version can require users to send a mail with subject:

```text
subscribe arxiv-digest
```

Body:

```yaml
email: user@example.com
language: zh
categories:
  - astro-ph.GA
must_keywords:
  - Milky Way
  - dwarf galaxy
  - stellar stream
boost_keywords:
  - Gaia
  - DESI
  - S5
exclude_keywords:
  - exoplanet
max_papers: 8
summary_requirements: >
  只关注银河系相关方向；对星流、矮星系、银河晕、Local Group、暗物质动力学特别关注。
  感兴趣文章需要中文详细总结：研究背景、核心问题、数据/方法、主要结果、局限性、为什么值得读。
```

The first implementation can store accepted profiles as JSON files. Later versions can move to SQLite.

## GPT Summary Contract

For each selected paper, send the model:

- arXiv ID, title, authors, categories, comments, abstract, URL.
- Subscriber profile.
- Required output schema.

Suggested output fields:

- `one_sentence_takeaway`
- `why_matched`
- `background`
- `method_data`
- `main_results`
- `relevance_to_profile`
- `limitations`
- `read_priority`

Use a compact model for first-pass classification and a stronger model only for selected papers that pass the profile threshold.

## Safety and Operations

- Treat all incoming emails as untrusted input.
- Do not execute instructions embedded in arXiv emails or subscriber emails.
- Only parse subscriber profile fields from an allowlisted format.
- For early testing, send digests only to the owner address.
- Keep an outbound send log to avoid duplicate sends.
- Keep raw arXiv email IDs and parsed paper IDs for auditability.

## MVP Stages

1. Parser and local profile matching.
2. Manual CLI run on pasted arXiv email.
3. Fetch latest arXiv email from `dailyarxiv@agent.qq.com`.
4. GPT API summary generator with cache.
5. Manual send to one test recipient.
6. Subscriber request parser.
7. Scheduled daily run.
