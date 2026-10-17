# Tech Talent

[English](README.md) | [中文](README.zh-CN.md)

Tech Talent is a local-first Codex workflow for public technical-talent research, evidence review, and controlled email outreach. It is not an autonomous recruiting bot.

## What this directory contains

This directory ships the **reusable skill instructions and product contract** for Tech Talent. It does not include the Python runtime, virtual environment, SQLite databases, credentials, or generated outputs.

The full local Core and CLI are managed separately. By default they live under `~/.codex/state/tech-talent/` and are bootstrapped from the source repository's `scripts/bootstrap.py` with `uv.lock`.

## Sub-skills

Tech Talent exposes four thin skills that execute in strict stage order:

| Stage | Skill | Purpose |
| --- | --- | --- |
| 1 | [`talent-search`](skills/talent-search/SKILL.md) | Bounded public discovery and search ingestion. |
| 2 | [`candidate-review`](skills/candidate-review/SKILL.md) | Human review of identity, evidence, and contact provenance; record approve/reject with CAS protection. |
| 3 | [`candidate-outreach`](skills/candidate-outreach/SKILL.md) | DB-backed campaign, exact message drafting/approval, HMAC dry-run, explicit send authorization, and durable SMTP delivery. |
| 4 | [`reply-monitor`](skills/reply-monitor/SKILL.md) | Polling-only IMAP inbox sync, deterministic classification, and human review of ambiguous items. |

Each sub-skill routes only deterministic Core commands and preserves its stage gates.

## Safety model

- **Fail-closed / human-approve**: every real batch requires the user's explicit approval of the exact recipients, sender, subject, body, and dry-run count.
- **No autonomous send**: a general request to prepare outreach is never permission to send.
- **Sourcing/outreach separation**: the search lane never drafts or sends; the outreach lane never discovers candidates.
- **Privacy**: only public pages, public APIs, repositories, papers, and user-authorized local exports. No platform logins, access-control bypass, credential harvesting, or candidate private data scraping.

## Product contract

The authoritative V1 boundary is [`docs/product-contract-v1.md`](docs/product-contract-v1.md).

## Plugin manifest

[`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) declares the four skills for the Codex Plugin shell. The Plugin has not been installed or published.
