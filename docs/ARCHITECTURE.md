# arXiv Digest Service Architecture

## Goal

Build a mailbox-driven daily arXiv digest service:

1. Subscribe `dailyarxiv@agent.qq.com` to arXiv daily `astro-ph`.
2. Parse the fixed-format daily arXiv email into structured paper records.
3. Maintain subscriber profiles from fixed-format request emails.
4. Broadly recall potentially relevant papers using categories, authors, keywords, and user interests.
5. Use a low-cost GPT API triage call to decide whether each recalled paper is `skip`, `short`, or `full_read`.
6. Generate personalized Chinese digests only for triage-approved papers.
7. Send each subscriber only the papers matching their direction and requirements.

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
  -> broad deterministic recall with profile signals
  -> GPT API relevance triage
  -> GPT API detailed summary generation
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
research_interests:
  - 银河系结构与形成演化
  - stellar halo
  - stellar streams
  - dwarf galaxies
favorite_authors:
  - Lina Necib
  - Ting S. Li
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
recall_limit: 40
ai_triage_threshold: 0.65
summary_requirements: >
  只关注银河系相关方向；对星流、矮星系、银河晕、Local Group、暗物质动力学特别关注。
  感兴趣文章需要中文详细总结：研究背景、核心问题、数据/方法、主要结果、局限性、为什么值得读。
```

The first implementation can store accepted profiles as JSON files. Later versions can move to SQLite.

## Relevance Triage Contract

The deterministic ranking stage is only a recall layer. It should be generous enough to avoid missing papers:

- include arXiv categories that the user accepts;
- add weak signals from user interests, keywords, and favorite authors;
- filter only hard exclusions;
- pass the top `recall_limit` papers to AI triage.

The AI triage model sees the full profile plus title, authors, categories, comments, abstract, URL, and recall signals. It returns:

- `action`: `skip`, `short`, or `full_read`
- `relevance_score`: 0 to 1
- `reason`: Chinese explanation of why the paper does or does not fit
- `matched_interests`: true semantic matches, not just raw keywords
- `concerns`: uncertainty or edge-case notes

This keeps keywords and author names useful as hints while letting the model decide semantic relevance.

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

Use a compact model for first-pass triage and a stronger model only for selected papers that pass the profile threshold. The prototype defaults to `OPENAI_TRIAGE_MODEL` or `gpt-5.4-mini`, and sends triage requests through the Responses API with low reasoning effort.

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
3. AI triage contract and OpenAI API triage call.
4. Fetch latest arXiv email from `dailyarxiv@agent.qq.com`.
5. GPT API summary generator with cache.
6. Manual send to one test recipient.
7. Subscriber request parser.
8. Scheduled daily run.
