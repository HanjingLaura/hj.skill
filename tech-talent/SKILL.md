---
name: tech-talent
description: Umbrella skill for local-first technical-talent research and controlled outreach. Use when a user wants to find public technical candidates, review evidence, prepare approved email outreach, or monitor replies.
---

# Tech Talent

Tech Talent is a local-first workflow for public technical-talent research, evidence review, and controlled email outreach. It is not an autonomous recruiting bot.

## When to use

Activate this skill when a user wants to:

- Discover public technical candidates by role, school, repository, paper, or research direction.
- Review candidate identity, evidence, and contact provenance and record human approve/reject decisions.
- Prepare, approve, and send controlled outreach emails to reviewed candidates.
- Monitor a mailbox for replies, bounces, and opt-outs after sending.

## Flow

The four sub-skills execute in strict stage order. Each gate must pass before the next stage begins:

```text
talent-search → candidate-review → candidate-outreach → reply-monitor
```

| Stage | Sub-skill | Purpose |
| --- | --- | --- |
| 1 | [`talent-search`](skills/talent-search/SKILL.md) | Bounded public discovery and search ingestion into the local DB. |
| 2 | [`candidate-review`](skills/candidate-review/SKILL.md) | Human review of identity, evidence, and contact provenance; record approve/reject with CAS protection. |
| 3 | [`candidate-outreach`](skills/candidate-outreach/SKILL.md) | DB-backed campaign creation, exact message drafting/approval, HMAC dry-run, explicit send authorization, and durable SMTP delivery. |
| 4 | [`reply-monitor`](skills/reply-monitor/SKILL.md) | Polling-only IMAP inbox sync, deterministic reply/bounce/opt-out classification, and human review of ambiguous items. |

## Safety principles

- **Fail-closed**: missing capability stops at an explicit stage gate. No silent fallback.
- **Human-approve**: every real batch requires the user's explicit approval of the exact recipients, sender, subject, body, and dry-run count.
- **No autonomous send**: a general request to prepare outreach is never permission to send. The agent must never fabricate approvals, confirmations, or credentials.
- **Sourcing/outreach separation**: the search lane never drafts or sends; the outreach lane never discovers candidates.
- **Privacy**: only public pages, public APIs, repositories, papers, and user-authorized local exports. No platform logins, access-control bypass, credential harvesting, or candidate private data scraping.

## Runtime note

The full local Core runtime (Python package, SQLite DB, CLI) lives under `~/.codex/state/tech-talent/` and is managed by the source repository's bootstrap. This skill directory ships only the reusable skill instructions and product contract; it does not include the Python runtime, venv, databases, credentials, or generated outputs.

See [`docs/product-contract-v1.md`](docs/product-contract-v1.md) for the authoritative V1 boundary.
