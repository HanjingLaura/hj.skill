---
name: reply-monitor
description: Poll one authorized IMAP INBOX, inspect campaign mailbox freshness, review ambiguous inbound events, reset a changed UIDVALIDITY epoch, and recover durable inbox-sync runs. Use when a user asks to check replies, bounces, opt-outs, or reply-monitor readiness.
---

# Reply Monitor

Use only the DB-backed `tech-talent inbox` commands. The monitor is a bounded, polling-only external read: it never runs a daemon, uses IMAP IDLE, marks messages as seen, or mutates the mailbox.

Resolve the managed runtime once. Do not rely on shell activation, repository cwd, or `PATH`:

```bash
TECH_TALENT="${TECH_TALENT_STATE_DIR:-$HOME/.codex/state/tech-talent}/venv/bin/tech-talent"
test -x "$TECH_TALENT" || { echo "tech-talent runtime missing; run scripts/bootstrap.py" >&2; exit 1; }
```

On Windows PowerShell, resolve the managed executable without activation or `PATH`:

```powershell
$TechTalentState = if ($env:TECH_TALENT_STATE_DIR) { $env:TECH_TALENT_STATE_DIR } else { "$HOME/.codex/state/tech-talent" }
$TECH_TALENT = Join-Path $TechTalentState "venv/Scripts/tech-talent.exe"
if (-not (Test-Path -LiteralPath $TECH_TALENT -PathType Leaf)) { throw "tech-talent runtime missing; run scripts/bootstrap.py" }
```

PowerShell must invoke the variable with `& $TECH_TALENT`; the remaining examples use the equivalent bash form `"$TECH_TALENT"`.

## 1. Preflight and external-read stage gate

Run `"$TECH_TALENT" db doctor`. If it returns `needs_setup`, run `"$TECH_TALENT" db init`; stop on `fail`.

Real IMAP synchronization reads a credentialed external mailbox. Run it only after the user authorizes the concrete mailbox/config and the named environment variables are already provisioned. Never ask the user to paste a password into chat, write credential values into a config or receipt, pass a password as a CLI argument, call IMAP directly, or claim a mailbox was checked from DB state alone.

## 2. Configure IMAP with native credential storage

Prefer the v2 config. For host, account, folder, and username lookups, the JSON contains environment variable names only; the password is retrieved from the operating system's native credential store:

```json
{
  "schema_version": "tech-talent.imap-config/v2",
  "host_env": "IMAP_HOST",
  "port_env": "IMAP_PORT",
  "security": "tls",
  "username_env": "GMAIL_USERNAME",
  "password_env": "",
  "credential_provider": "system_keyring",
  "credential_service": "tech-talent-plugin.gmail",
  "account_email_env": "IMAP_ACCOUNT_EMAIL",
  "folder_env": "IMAP_FOLDER",
  "timeout_seconds": 30,
  "max_messages_per_sync": 100,
  "max_message_bytes": 1048576,
  "local_test_only": false
}
```

The strict environment-only `tech-talent.imap-config/v1` schema remains supported for existing installations. It uses `password_env` and omits `credential_provider` and `credential_service`. In v2 `system_keyring` mode, `password_env` must be empty. When SMTP and IMAP use the same account, their v2 configs must use the same `credential_service` and resolve `username_env` to the same username, so one stored credential serves both protocols.

Only after the user authorizes the concrete local credential-store change, read the password from an already provisioned environment variable and require the exact confirmation shown below. The password value must never be placed in a command argument or printed:

```bash
export CREDENTIAL_SERVICE="tech-talent-plugin.gmail"
"$TECH_TALENT" credential status --service "$CREDENTIAL_SERVICE" --username-env GMAIL_USERNAME
"$TECH_TALENT" credential store --service "$CREDENTIAL_SERVICE" --username-env GMAIL_USERNAME --password-env GMAIL_APP_PASSWORD --confirmation "STORE CREDENTIAL $CREDENTIAL_SERVICE $GMAIL_USERNAME"
```

`store` creates only when the service/username item is absent and otherwise fails closed. Replacing an existing item requires separate user authorization, `--replace`, and the exact case-sensitive confirmation `REPLACE CREDENTIAL <service> <username>`:

```bash
"$TECH_TALENT" credential store --service "$CREDENTIAL_SERVICE" --username-env GMAIL_USERNAME --password-env GMAIL_APP_PASSWORD --replace --confirmation "REPLACE CREDENTIAL $CREDENTIAL_SERVICE $GMAIL_USERNAME"
```

`status` reports only non-secret metadata. Delete a credential only when the user explicitly requests it, using the exact case-sensitive confirmation:

```bash
"$TECH_TALENT" credential delete --service "$CREDENTIAL_SERVICE" --username-env GMAIL_USERNAME --confirmation "DELETE CREDENTIAL $CREDENTIAL_SERVICE $GMAIL_USERNAME"
```

Credential service names must use the `tech-talent-plugin.` namespace. `system_keyring` accepts Windows Credential Manager, macOS Keychain, and supported native Linux Secret Service/libsecret backends. It fails closed for plaintext, null/fail, and fallback backends such as `keyrings.alt`. Secret values never belong in JSON, CLI arguments, the database, logs, receipts, or chat. After a successful store, the temporary password environment variable may be removed.

V1 supports exactly `INBOX`. Real providers require `tls` or `starttls` with the default certificate verifier. `plain_loopback` is test-only, requires an exact loopback host plus `local_test_only=true`, and permits no credentials. OAuth, provider-specific labels, and multiple folders are outside this milestone.

The outreach Core uses this monitored account as the RFC 5321 envelope-from as well as the campaign `Reply-To` destination. A real-provider preflight must confirm that both human replies and delivery-status notifications are delivered into this exact `INBOX`; a provider that routes either stream elsewhere is not V1-compatible.

## 3. Poll one bounded UID prefix

After the external-read stage gate passes, run one explicit poll and persist its durable receipt:

```bash
"$TECH_TALENT" inbox sync --imap-config "$IMAP_CONFIG_JSON" --receipt "$INBOX_RECEIPT"
```

The Core selects `INBOX` with `readonly=True`, searches by UID, and fetches with `BODY.PEEK` under configured message-count and byte bounds. It stores minimized canonical observations and digests, not full raw MIME or message bodies. If the server-reported message size exceeds `max_message_bytes`, the bounded prefix is forced to `needs_review` with `message_exceeds_byte_limit`; it can never create a deterministic effect. Every cross-UID oversized observation remains a separate canonical item, so it is never duplicate-folded even when its bounded prefix and inbound Message-ID match another UID. A `partial`, `failed`, `uidvalidity_reset`, or recovered run does not create fresh monitor state.

## 4. Check the campaign send gate offline

Resolve the monitor from the campaign's exact `reply_to` without accessing IMAP:

```bash
"$TECH_TALENT" inbox status --campaign-id "$CAMPAIGN_ID"
```

Sending may proceed only when `monitor_status=ready`, `fresh=true`, the cursor is coherent, there is no active sync/reset, and `relevant_pending_review=0`. Any unresolved `message_exceeds_byte_limit` item is a mailbox-global pending blocker for every campaign using that monitored account, even when no recipient or thread association survived truncation. A completed sync is fresh for 15 minutes. The DB-backed outreach dry-run and send preflight re-check this state; a printed status result is not reusable authority.

## 5. Review ambiguous observations with CAS

List pending `needs_review` items offline. Use `--mailbox-key` when the user selected one mailbox; use `--all` only for audit history:

```bash
"$TECH_TALENT" inbox review list --mailbox-key "$MAILBOX_KEY"
"$TECH_TALENT" inbox review list --mailbox-key "$MAILBOX_KEY" --all
```

Show the exact item, `item_digest`, proposed classification, and outbound `message_id` to a human. Never infer or fabricate the decision. For a non-ignored decision, require the exact case-sensitive confirmation `APPLY <item_id> <classification> <message_id>`:

```bash
"$TECH_TALENT" inbox review decide --item-id "$ITEM_ID" --expected-item-digest "$ITEM_DIGEST" --classification "$CLASSIFICATION" --message-id "$MESSAGE_ID" --decided-by "$REVIEWER" --confirmation "APPLY $ITEM_ID $CLASSIFICATION $MESSAGE_ID"
```

For an intentionally ignored item, omit `--message-id` and require the literal `IGNORE` token:

```bash
"$TECH_TALENT" inbox review decide --item-id "$ITEM_ID" --expected-item-digest "$ITEM_DIGEST" --classification ignored --decided-by "$REVIEWER" --confirmation "APPLY $ITEM_ID ignored IGNORE"
```

The digest is compare-and-swap protection. If it is stale or the item was already decided, list the item again; do not replay the old decision. An oversized item may be resolved only by this exact human CAS: either bind it to an outbound current revision with durable `accepted` or `delivery_unknown` provenance, or classify it as `ignored` with the literal `IGNORE` confirmation.

## 6. Handle UIDVALIDITY changes explicitly

A changed UIDVALIDITY epoch stops before search/fetch, preserves the old cursor, and sets `reset_required`. Inspect the sync receipt and status, show the detected mailbox key and new UIDVALIDITY to the user, then require exact case-sensitive authorization:

```bash
"$TECH_TALENT" inbox cursor reset --mailbox-key "$MAILBOX_KEY" --new-uidvalidity "$NEW_UIDVALIDITY" --authorized-by "$OPERATOR" --confirmation "RESET $MAILBOX_KEY $NEW_UIDVALIDITY"
```

Reset starts a new generation and requires a fresh bounded rescan. It never treats the new epoch as already checked.

## 7. Inspect and recover durable runs offline

Run inspection never accesses IMAP:

```bash
"$TECH_TALENT" inbox run list --unresolved
"$TECH_TALENT" inbox run show --run-id "$RUN_ID" --receipt "$RUN_RECEIPT"
```

After a confirmed process crash, recovery finalizes durable facts without fetching, advancing the cursor, or creating freshness. Require the exact confirmation `RECOVER INBOX <run_id>`:

```bash
"$TECH_TALENT" inbox run recover --run-id "$RUN_ID" --confirmation "RECOVER INBOX $RUN_ID" --receipt "$RECOVERY_RECEIPT"
```

## Classification and effect boundary

- Association is exact and deterministic: `In-Reply-To`, `References`, or structured DSN linkage to a persisted outbound RFC Message-ID. Subject, display name, sender similarity, and model judgment are never identity keys.
- A malformed Message-ID, Subject, MIME structure, or thread header forces `needs_review`, but independently strict-valid provenance fields are retained for review; one defective field never authorizes erasing another validated From, recipient, subject, inbound Message-ID, or exact association field.
- Deterministic classes are `reply`, `opt_out`, `out_of_office`, `hard_bounce`, and `soft_bounce`; unsupported or ambiguous evidence becomes `needs_review`.
- `opt_out` and `hard_bounce` create permanent suppression/contact effects. They are never undone by a later ordinary reply.
- `out_of_office` and `soft_bounce` are recorded events but do not create a terminal message state or permanent suppression. V1 never schedules or sends an automatic follow-up.
- Relevant pending review, stale/missing freshness, an active/recovered/partial run, cursor mismatch, or `reset_required` is a fail-closed send blocker.

## Deferred provider and automation gates

The G006 acceptance surface is fake-client and local loopback IMAP only. It does not claim a real Gmail, Outlook, or university-provider smoke test. DKIM verification, OAuth/XOAUTH2, IMAP IDLE/push, background scheduling, multiple folders, provider-specific labels, automated follow-up, Plugin installation, and publication remain separate release gates.
