# Tech Talent V1 Product Contract

This document is the authoritative V1 boundary. It defines the intended product behavior; a documented state or command must not be presented as implemented until its code and acceptance test exist.

## Product and support boundary

- Tech Talent is a local-first Codex workflow for public technical-talent research, human review, and controlled outreach. It is not an autonomous recruiting bot.
- V1 acceptance covers macOS 14+ and Windows 10+ with Python 3.11-3.13. Linux portability is desirable but is not a release gate.
- The supported runtime is created by `scripts/bootstrap.py` from `uv.lock` under `~/.codex/state/tech-talent/venv`. Bootstrap first provisions the locked runtime and build-backend group, then installs `tech-talent` non-editably with build isolation and build-step network access disabled. Warm-cache `--offline` installation is a release gate.
- A clean bootstrap reports `needs_setup` until `tech-talent db init` has created and migrated the local database. Doctor must never report an absent database as a pass.
- Search reasoning may be probabilistic. Identity, approval, suppression, receipt verification, sending, and accounting must be implemented in deterministic code and fail closed.
- Milestone status: G007 is a verified local release-candidate boundary. Candidate review, approved outreach, durable SMTP delivery/recovery, and bounded IMAP monitoring are implemented; the packaged source, clean extraction, locked non-editable install, source-move survival, aggregate gold evaluation, and one-database SMTP-to-IMAP socket canary are acceptance gates. No real email provider, real candidate send, Codex Plugin installation, or publication is claimed.

## Data and evidence boundary

- Allowed inputs are public pages, public APIs, public repositories and papers, and local exports explicitly authorized and supplied by the user.
- The system must not log in to recruiting platforms, bypass access controls, scrape private candidate data, or collect secrets from source pages.
- Search results are discovery hints, not final evidence. Sendable identity and contact claims require a traceable first-party or otherwise authoritative public source.
- Data must be minimized to recruiting relevance. Credentials remain in environment variables or an operating-system secret store and must never enter repository files, candidate exports, logs, or receipts.
- A contact point has one of these states: `public_verified`, `user_authorized`, `inferred_unverified`, `bounced`, or `suppressed`.
- `inferred_unverified` is research-only and is always non-sendable. V1 does not guess an address and treat it as verified.
- Legacy candidate import is research-only and cannot create `public_verified` or `user_authorized` state. Those trusted states require `tech-talent search ingest` to bind the exact claim to a validated public artifact or matching user-authorized local file.

## Local state and migration contract

- The new deterministic Core uses SQLite at `~/.codex/state/tech-talent/talent.db` as its canonical state store. `--db` and `TECH_TALENT_DB` may select another local path.
- Every connection enables WAL, foreign keys, and a 5-second busy timeout. POSIX state directories are `0700`; databases and backups are `0600`.
- SQL migrations are contiguous, versioned, and SHA-256 checksum verified. Existing databases receive a timestamped SQLite backup-API snapshot before an upgrade. A migration and its `schema_migrations` receipt are one transaction; failure rolls both back.
- The schema includes candidates, identities, evidence, contact points, campaigns, messages, approvals, mail events, suppression, generation-bound mailbox cursors, inbox sync runs/items/reviews/UIDVALIDITY resets, contact history, import runs/items, and audit events with foreign-key, append-only, and deduplication constraints.
- Database constraints make `inferred_unverified`, `bounced`, and `suppressed` contact points non-sendable even if a caller attempts to set `sendable=1`.
- `tech-talent import candidates|suppression|contacted` is whole-file transactional and idempotent by source SHA-256 plus canonical row fingerprint. Candidate schema v1 Markdown, CSV, and JSONL are accepted. Arbitrary extra candidate fields are discarded rather than persisted. Candidate import rejects attempts to promote a legacy contact to `public_verified` or `user_authorized`.
- All CLI results use the `tech-talent.command-result/v1` JSON contract. Missing initialization is `needs_setup`, not `pass` or an empty success.
- Legacy files remain import/export artifacts during migration. The legacy `send_outreach.py --send` flag is permanently disabled; its preparation and network-free dry-run artifacts are not DB approvals or send authority. Live delivery belongs only to the SQLite-backed `tech-talent outreach send` path.
- Exactly one writable authoritative database lineage may be active. Backups and clones must remain offline/read-only. Replay prevention is authoritative within one writable SQLite lineage; promoting a restore or clone requires retiring the old writer, rotating the outreach HMAC secret, and issuing fresh dry-run/authority receipts.

## Plugin shell boundary

- The repository includes a local Codex Plugin manifest and four thin skills: `talent-search`, `candidate-review`, `candidate-outreach`, and `reply-monitor`.
- The Plugin shell declares no MCP server, app, or hook. It has not been installed, added to a marketplace, or published by this milestone.
- A skill may call only a real, deterministic `tech-talent` command. The implemented command surface includes database initialization/readiness/backup, the three legacy imports, bounded offline `search ingest`/`search show`, candidate show/decide, campaign create/show/cancel, message draft/list/show/revise, outreach validate/approve/dry-run/authorize-send/send/run inspection/recovery, credential status/store/delete, plus `tech-talent inbox sync`, `tech-talent inbox status`, review list/decide, cursor reset, and inbox run list/show/recover.
- Codex may use available public search capabilities to assemble a bounded offline packet. The Core performs no network discovery, and no discovery result becomes persisted truth without strict packet, artifact-digest, claim-attribution, and coverage validation.
- Human candidate approve/reject persistence, controlled outbound outreach, and G006 mailbox monitoring are implemented. Identity-conflict merge/resolution mutation remains unavailable until its separate Core command and acceptance tests exist.
- Missing capability must stop at an explicit stage gate. A skill must not bypass deterministic search ingestion, substitute the disabled legacy SMTP route, bypass `tech-talent inbox` with direct IMAP access, fabricate a human decision/approval/confirmation, or claim Plugin/provider completion without a command receipt and matching acceptance evidence.

## Search and coverage semantics

- Every run uses a bounded frontier: explicit channels, query limits, page limits, time budgets, and failure recording.
- Search packet V1 accepts only `frontier_result`, `search_hit`, `source_artifact`, and `candidate_claim` events. Every source artifact is bound by exact lowercase SHA-256 and byte count; trusted identity or contact claims must also bind exact candidate attribution and claim value.
- `complete` means the declared bounded frontier finished. It never means the entire public web was exhaustively scanned.
- `partial` means one or more declared channels, queries, or pages were not completed because of a limit, timeout, rate limit, parsing failure, or unavailable source.
- `fail` means no trustworthy result contract can be produced. A failed or partial run must not be relabeled as complete because some candidates were found.
- Duplicate or same-name identities with conflicting affiliation, repository, paper, or contact evidence require human review; weak similarity must not trigger an automatic merge.

## Evaluation contract

- Search quality is evaluated offline and deterministically against versioned synthetic gold sets for `department`, `github`, and `paper`, with at least 36 candidates per channel. The evaluator is an acceptance-test and receipt surface, not a Plugin command.
- Release gates cover candidate and verified-contact recall, candidate/contact/identity precision, top-20 and top-100 recall, duplicate rate, false merges, provenance completeness, and coverage accuracy.
- The current three-channel ingestion fixture persists 108 candidates and must pass every gate. Evaluation inputs, metrics, thresholds, and the canonical receipt are digest-bound and fail closed on malformed or ambiguous data.
- Inbound association/classification is evaluated offline against a versioned synthetic corpus of at least 60 messages. Release gates require exact-association precision of 100%, zero false suppressions, supported deterministic recall of at least 95%, and unsupported-to-review recall of 100%.
- `scripts/run_evaluations.py --require-installed` must execute both gold evaluations through the active-prefix non-editable package, deny all DNS/socket operations at the lowest Python socket surfaces, and emit one stable digest-bound machine receipt.
- `scripts/run_local_canary.py --require-installed` must use one fresh authoritative SQLite lineage, one real stdlib SMTP socket, and two real stdlib IMAP read-only sessions. It may connect only to the exact two ephemeral literal-IPv4 `127.0.0.1` endpoints created by that invocation, must use synthetic `.test` identities and no credentials, and must end with one accepted outbound, one exactly linked inbound reply, message state `replied`, zero pending review, and zero active suppression.

## Candidate and message states

Candidate lifecycle:

```text
discovered -> enriched -> needs_review -> approved | rejected
```

Message lifecycle:

```text
draft -> approved -> dry_run_passed
      -> sent | failed | delivery_unknown
      -> replied | opted_out | bounced
```

- `delivery_unknown` is not `failed`: the system must not retry automatically because delivery may already have occurred.
- A reply, opt-out, hard bounce, or suppression event stops automated follow-up eligibility. `out_of_office` and `soft_bounce` are recorded but do not create a terminal message state or permanent suppression.
- State transitions require durable evidence or an explicit human action; prompt text alone cannot mutate trusted state.

## Inbox monitoring boundary

- V1 monitoring is explicit polling only. `tech-talent inbox sync` performs one bounded external mailbox read; it does not install a scheduler, run a daemon, use IMAP IDLE, or trigger follow-up.
- Strict IMAP config JSON stores environment-variable names plus non-secret credential-provider metadata, never credential values. The environment-only `tech-talent.imap-config/v1` schema remains supported. The recommended v2 schema uses `credential_provider=system_keyring`, an empty `password_env`, and a `credential_service` in the `tech-talent-plugin.` namespace; endpoint/account/folder/username values still come from named environment variables. Native Windows Credential Manager, macOS Keychain, and supported Linux Secret Service/libsecret backends are accepted; plaintext, null/fail, and fallback backends such as `keyrings.alt` fail closed. Real access requires `tls` or `starttls` with normal certificate verification; plaintext is limited to credential-free exact loopback tests.
- V1 monitors exactly `INBOX`, selects it read-only, searches by UID, and fetches bounded content with `BODY.PEEK`. It never uses `STORE`, `CLOSE`, or `EXPUNGE`, marks messages as seen, or persists full raw MIME/body content.
- A server-reported message larger than `max_message_bytes` is persisted only as a minimized `needs_review` observation with reason `message_exceeds_byte_limit`. It produces no deterministic effect, is never cross-UID duplicate-folded, and every UID remains independently accountable even when bounded prefixes and inbound Message-ID values match.
- Cursor identity binds account, endpoint, folder, generation, UIDVALIDITY, and UID high-water state. A UIDVALIDITY mismatch stops before search/fetch, preserves the prior cursor, records `reset_required`, and requires the exact `RESET <mailbox_key> <new_uidvalidity>` authorization before a new-generation bounded rescan.
- Inbound association is exact: `In-Reply-To`, `References`, or structured DSN linkage must match a persisted outbound RFC Message-ID. Subject, display name, sender similarity, body wording, and model judgment are never association keys.
- Malformed Message-ID, Subject, MIME, or thread evidence forces `needs_review`, while every independently strict-valid provenance field remains available for human review. Provenance parsing is field-local rather than all-or-nothing.
- Deterministic classifications are `reply`, `opt_out`, `out_of_office`, `hard_bounce`, and `soft_bounce`. Unsupported or ambiguous evidence is `needs_review`; a human decision requires the current `item_digest`, an explicit outbound message binding unless ignored, and exact `APPLY <item_id> <classification> <message_id>` or `APPLY <item_id> ignored IGNORE` confirmation.
- Every unresolved `message_exceeds_byte_limit` item is a mailbox-global pending blocker for all campaigns sharing the monitored account. It may be resolved only by exact human CAS, either ignored or bound to a current outbound revision with durable `accepted` or `delivery_unknown` provenance.
- `opt_out` and `hard_bounce` create permanent suppression/contact effects. `out_of_office` and `soft_bounce` create non-terminal events only. A later ordinary reply cannot silently reverse a permanent suppression.
- Only a coherent finalized `complete` sync may set freshness, for at most 15 minutes. Partial, failed, recovered, reset-required, running, stale, missing, reply-to-mismatched, truth-mismatched, or relevant-review-pending monitor state blocks outreach.
- Inbox run recovery requires `RECOVER INBOX <run_id>` and only finalizes durable facts. It never reconnects, fetches, advances the cursor, or creates freshness.

## Sending boundary and preserved baseline invariants

- Sourcing never drafts or sends messages. Outreach never discovers new candidates.
- Real sending requires explicit human approval of the exact recipient, sender, subject, and body.
- Any approved-content change invalidates the approval digest and requires a new review.
- A real send requires a matching HMAC-signed dry-run receipt, a short-lived one-shot send authority, the exact case-sensitive `SEND <campaign_id> <count>` confirmation, and the explicit `--execute` switch. General permission to prepare outreach is not permission to send a batch.
- Dry-run and authority receipts bind the authoritative DB instance, campaign configuration, exact revisions/approvals/candidate decisions, validation snapshot, recipient count, UTC day, purpose, expiry, and parent receipt. Authority consumption and the complete set of durable reservations commit atomically.
- Every eligible item also binds the campaign `reply_to` monitor snapshot and pending-review digest. Dry-run, authority issuance, send-run reservation, and each SMTP attempt re-check canonical monitor truth; pre-G006 or stale monitor snapshots cannot authorize delivery.
- Suppressed, blocked, unverified, or recently contacted recipients are not eligible for sending.
- Pilot mode hard-caps each campaign batch at 20 and globally caps the authoritative database at 20 durable UTC-day reservations, across all campaigns and senders.
- Strict SMTP config JSON stores environment-variable names plus non-secret credential-provider metadata, never credential values. The environment-only `tech-talent.smtp-config/v1` schema remains supported. The recommended v2 schema uses `credential_provider=system_keyring`, an empty `password_env`, and a `credential_service` in the `tech-talent-plugin.` namespace. Explicitly authorized v3 adds an unauthenticated SOCKS5 route whose resolved endpoint must be exact loopback; it performs remote DNS, preserves SMTP-target TLS verification, and never falls back to direct delivery. SMTP and IMAP may share one native credential only when both configs use the same service and resolve to the same username. TLS or STARTTLS is required for real SMTP; plaintext is limited to credential-free exact loopback testing.
- Credential status returns only non-secret metadata. Store reads the password from the named environment variable, creates only when the service/username item is absent, and requires exact `STORE CREDENTIAL <service> <username>` confirmation. Replacement fails closed unless `--replace` and exact `REPLACE CREDENTIAL <service> <username>` confirmation are both supplied. Deletion requires exact `DELETE CREDENTIAL <service> <username>` confirmation. Password values must never appear in JSON, CLI arguments, DB state, logs, receipts, or chat.
- The RFC 5321 envelope-from is the campaign's exact monitored `reply_to`; the RFC 5322 `From` header remains `sender_email`. Real-provider acceptance requires both human replies and delivery-status notifications to arrive in that same monitored `INBOX`.
- SMTP connection, greeting, EHLO, TLS, and authentication complete before any authority consumption or reservation. Each reservation becomes durably `attempting` before its network call, then ends as `accepted`, `failed`, `delivery_unknown`, or `not_attempted`.
- Every planned message must produce exactly one explicit terminal run outcome. The count conservation equations are `planned = attempted + not_attempted` and `attempted = accepted + failed + delivery_unknown` on success, partial SMTP failure, and recovery paths.
- Crash recovery never reconnects or resends: unresolved `attempting` becomes `delivery_unknown`, while an unstarted reservation becomes `not_attempted`.
- V1 follow-ups are suggestions only. Each new outbound message requires a new approval; inbox events never schedule or send one automatically.

## Local release and share contract

- `scripts/release_verify.py` is the only V1 release-candidate publisher. `verified_local_release_candidate` requires every named `local_gates` entry to pass in one invocation; missing scripts, malformed JSON, zero tests, skips, source drift, archive drift, extraction failure, bootstrap failure, evaluation failure, or canary failure fail closed.
- The share archive is built from an explicit product-path allowlist. Generated state, `.git`, `.omx`, virtual environments, caches, `*.egg-info`, symlinks, secret-like names, private directories, and candidate/contact/cohort data probes are excluded or rejected before packaging.
- The file manifest binds every relative path, normalized mode, byte count, and SHA-256. ZIP members use stable order, fixed timestamps, normalized modes, and deterministic storage; two builds in the same release invocation must be byte-identical.
- The release-tested source digest must equal the packaged digest. The archive is extracted with traversal, duplicate-member, file-type, mode, size, and digest checks, then the complete fail-closed suite runs from that clean extraction with zero skips.
- A fresh locked non-editable runtime is bootstrapped from the extraction. Aggregate evaluation and local canary run with that runtime's interpreter and must prove `runtime.installed_non_editable=true`. The extracted source is then moved away; the installed import, CLI, DB initialization, and doctor must still pass.
- A successful release publishes only the versioned ZIP, source manifest, checksum sidecar, and canonical signed receipt. Successful receipt content is path-stable and must not contain temporary absolute paths or secrets.
- Official Plugin/Skill validation is `deferred_unavailable` when its managed scripts cannot be discovered. Actual Codex installation, marketplace/publication, real SMTP/IMAP provider smoke tests, and every real-candidate send remain `deferred_authority`; no local gate may relabel them as passed.
- Architecture evidence is indexed by `docs/architecture-invariants-v1.md`. Any real pilot is governed separately by `docs/real-pilot-protocol-v1.md`: 100-person no-send shadow review, then independently approved maximum batches `5 -> 10 -> 20`, with mandatory stop conditions and no automatic follow-up.

## Privacy, retention, and operator responsibility

- Repository-local candidate inputs, JDs, allowlists, suppression data, queues, and logs belong only under ignored `outputs/` or `local-data/` paths.
- Operators are responsible for lawful purpose, sender identity, jurisdiction-specific notice, and honoring opt-outs.
- Deletion/export controls remain a later V1 goal. Current Markdown/CSV/JSONL files are local transitional artifacts and must not be described as a production database.

## Non-goals

- A hosted SaaS, central candidate database, generic ATS, or shared cross-user suppression service.
- Fully autonomous candidate decisions, real sends, or follow-up sequences.
- Exhaustive "scan the whole web" claims.
- Email guessing as a sendable contact source.
- Private-platform automation, credential harvesting, CAPTCHA bypass, or access-control circumvention.
- MCP server, web dashboard, Plugin installation, marketplace registration, or publication.
- DKIM verification, OAuth/XOAUTH2, IMAP IDLE/push, background scheduling, multiple folders, provider-specific labels, and real Gmail/Outlook/university-provider smoke certification. These remain separate authority gates; G007 evidence is installed-package, synthetic-gold, and exact-loopback only.
