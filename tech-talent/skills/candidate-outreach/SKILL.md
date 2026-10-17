---
name: candidate-outreach
description: Build, approve, dry-run, explicitly authorize, send, inspect, and recover DB-backed candidate outreach. Use for a reviewed campaign whose candidates and exact messages are ready for deterministic safety gates.
---

# Candidate Outreach

Use only the DB-backed `tech-talent outreach` workflow. Email sending is an external side effect: a general request to prepare outreach is not permission to send, and every real batch requires the user's explicit approval of that concrete dry-run recipient count.

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

## 1. Preflight and safety state

Run `"$TECH_TALENT" db doctor`. If it returns `needs_setup`, run `"$TECH_TALENT" db init`; stop on `fail`.

Import user-supplied safety ledgers before campaign work when they exist:

```bash
"$TECH_TALENT" import suppression "$SUPPRESSION_TXT"
"$TECH_TALENT" import contacted "$CONTACTED_JSONL"
```

Only candidates with a current human `approved` decision and a bound `public_verified` or `user_authorized` sendable email can pass validation. Outreach never discovers candidates or upgrades contact provenance.

## 2. Create and inspect a campaign

Create an immutable sender/cooldown configuration. `MAX_SEND` must be from 1 to 20:

```bash
"$TECH_TALENT" outreach campaign create --name "$CAMPAIGN_NAME" --sender-email "$SENDER_EMAIL" --sender-name "$SENDER_NAME" --reply-to "$REPLY_TO" --max-send "$MAX_SEND" --cooldown-days "$COOLDOWN_DAYS" --created-by "$CREATOR"
"$TECH_TALENT" outreach campaign show --campaign-id "$CAMPAIGN_ID"
```

Cancellation is terminal and prevents remaining delivery work:

```bash
"$TECH_TALENT" outreach campaign cancel --campaign-id "$CAMPAIGN_ID"
```

## 3. Draft, inspect, and revise exact messages

Each draft/revision input is one strict JSON object with no extra keys:

```json
{
  "schema_version": "tech-talent.outreach-message/v1",
  "candidate_id": "candidate-id",
  "contact_point_id": "contact-point-id",
  "recipient_email": "candidate@example.edu",
  "subject": "Specific research opportunity",
  "body": "Personalized plain-text body without unresolved placeholders."
}
```

```bash
"$TECH_TALENT" outreach message draft --campaign-id "$CAMPAIGN_ID" --input "$MESSAGE_JSON" --drafted-by "$DRAFTER"
"$TECH_TALENT" outreach message list --campaign-id "$CAMPAIGN_ID"
"$TECH_TALENT" outreach message show --message-id "$MESSAGE_ID"
"$TECH_TALENT" outreach message revise --message-id "$MESSAGE_ID" --input "$REVISION_JSON" --expected-content-digest "$CONTENT_DIGEST" --revised-by "$REVIEWER"
```

A revision is append-only and compare-and-swap protected. Any content change invalidates the prior approval and requires a new validation, human approval, dry-run, and send authority.

## 4. Validate and record exact human approvals

Validate every campaign message before approval:

```bash
"$TECH_TALENT" outreach validate --campaign-id "$CAMPAIGN_ID"
```

The human approval file binds every selected message to the digest shown during review:

```json
{
  "schema_version": "tech-talent.outreach-approval/v1",
  "campaign_id": "campaign-id",
  "approved_by": "human-reviewer",
  "note": "Reviewed exact recipient, sender, subject, and body.",
  "items": [
    {
      "message_id": "message-id",
      "expected_content_digest": "lowercase-64-character-sha256"
    }
  ]
}
```

```bash
"$TECH_TALENT" outreach approve --input "$APPROVAL_JSON"
```

Do not create approval JSON from ranking output or agent judgment. The named human must review the exact copy and recipient set.

## 5. Require a fresh reply monitor

The campaign's exact `reply_to` must resolve to one monitored `INBOX`. Check the DB-authoritative state without accessing IMAP:

```bash
"$TECH_TALENT" inbox status --campaign-id "$CAMPAIGN_ID"
```

Stop unless `monitor_status=ready`, `fresh=true`, and `relevant_pending_review=0`. If the monitor is missing, stale, running, awaiting a UIDVALIDITY reset, or has relevant `needs_review` items, open `skills/reply-monitor/SKILL.md` and resolve that stage gate. Real `inbox sync` is a credentialed external read and requires the user's authorization of the concrete mailbox/config. One completed sync is fresh for 15 minutes; status, dry-run, and send all re-check canonical DB state.

## 6. Dry-run and obtain concrete batch authorization

Keep the HMAC secret only in an environment variable; it must contain at least 32 characters and must not enter config files, logs, receipts, or the repository:

```bash
export TECH_TALENT_OUTREACH_SECRET="<private-random-value>"
"$TECH_TALENT" outreach dry-run --campaign-id "$CAMPAIGN_ID" --receipt "$DRY_RUN_RECEIPT"
```

Show the user the exact dry-run recipients and `EXACT_COUNT`. Stop at the external-side-effect stage gate until the user explicitly approves this concrete batch. After that approval, use the exact case-sensitive confirmation `SEND <campaign_id> <count>`:

```bash
"$TECH_TALENT" outreach authorize-send --campaign-id "$CAMPAIGN_ID" --dry-run-receipt "$DRY_RUN_RECEIPT" --authority-receipt "$AUTHORITY_RECEIPT" --confirmation "SEND $CAMPAIGN_ID $EXACT_COUNT"
```

Dry-run receipts expire after 24 hours; send authorities expire after 15 minutes. A changed campaign, decision, message, approval, suppression state, cooldown eligibility, reply-monitor snapshot, pending review set, or count invalidates the authority.

## 7. Configure SMTP with native credential storage

Prefer the v2 config. Endpoint/account values remain behind environment-variable names, while the password is retrieved from the operating system's native credential store:

```json
{
  "schema_version": "tech-talent.smtp-config/v2",
  "host_env": "SMTP_HOST",
  "port_env": "SMTP_PORT",
  "security": "starttls",
  "username_env": "GMAIL_USERNAME",
  "password_env": "",
  "credential_provider": "system_keyring",
  "credential_service": "tech-talent-plugin.gmail",
  "timeout_seconds": 30,
  "local_test_only": false
}
```

The strict environment-only `tech-talent.smtp-config/v1` schema remains supported for existing installations. It uses `password_env` and omits `credential_provider` and `credential_service`. In v2 `system_keyring` mode, `password_env` must be empty. Use the same `credential_service` and resolved username in the IMAP config when both protocols use one account.

When the user explicitly authorizes an application-scoped local SOCKS route, use v3. It preserves the v2 credential fields and adds only non-secret proxy metadata and environment-variable names:

```json
{
  "schema_version": "tech-talent.smtp-config/v3",
  "host_env": "SMTP_HOST",
  "port_env": "SMTP_PORT",
  "security": "starttls",
  "username_env": "GMAIL_USERNAME",
  "password_env": "",
  "credential_provider": "system_keyring",
  "credential_service": "tech-talent-plugin.gmail",
  "proxy_type": "socks5",
  "proxy_host_env": "SMTP_PROXY_HOST",
  "proxy_port_env": "SMTP_PROXY_PORT",
  "timeout_seconds": 30,
  "local_test_only": false
}
```

V3 permits only an unauthenticated SOCKS5 proxy on the exact loopback hosts `127.0.0.1`, `::1`, or `localhost`, and only with `tls` or `starttls`. It performs remote DNS through the proxy, retains the SMTP target for TLS SNI and hostname verification, and never falls back to a direct connection. Never infer proxy authorization from a general send request.

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

Use `tls` or `starttls` for real SMTP. `plain_loopback` is permitted only with an exact loopback host, `local_test_only=true`, and no credentials. Do not place SMTP hostnames, usernames, passwords, or secret values in the JSON file.

The Core uses the campaign's exact `reply_to` as the RFC 5321 envelope-from while preserving `sender_email` in the human-visible RFC 5322 `From` header. Before a real send, verify that the provider accepts this reverse-path and delivers both human replies and delivery-status notifications to that monitored `INBOX`; otherwise stop before authorization.

## 8. Execute the approved batch

The same exact confirmation is required again, and `--execute` has no implicit or `--yes` substitute:

```bash
"$TECH_TALENT" outreach send --campaign-id "$CAMPAIGN_ID" --authority-receipt "$AUTHORITY_RECEIPT" --smtp-config "$SMTP_CONFIG_JSON" --confirmation "SEND $CAMPAIGN_ID $EXACT_COUNT" --executed-by "$OPERATOR" --receipt "$SEND_RECEIPT" --execute
```

The authoritative DB enforces a global UTC daily reservation cap of 20, not merely a per-campaign or per-sender limit. SMTP setup completes before authority consumption or reservation. Before each attempt, the Core re-checks the exact monitor snapshot and the DB trigger enforces a fresh, coherent reply monitor; a stale/reset/running/review-pending monitor produces `not_attempted`. Every reserved item ends as `accepted`, `failed`, `delivery_unknown`, or `not_attempted`, with count conservation. `delivery_unknown` means delivery may already have happened and must never be retried automatically.

## 9. Inspect and recover durable runs

Inspection is offline:

```bash
"$TECH_TALENT" outreach run list --unresolved
"$TECH_TALENT" outreach run show --run-id "$RUN_ID" --receipt "$RUN_RECEIPT"
```

After a confirmed process crash, recovery only finalizes durable facts; it never reconnects or resends. It converts a durable `attempting` item to `delivery_unknown` and an unstarted reservation to `not_attempted`:

```bash
"$TECH_TALENT" outreach run recover --run-id "$RUN_ID" --recovered-by "$OPERATOR" --confirmation "RECOVER $RUN_ID" --receipt "$RECOVERY_RECEIPT"
```

## Authoritative DB and replay boundary

Maintain exactly one active writable authoritative database lineage. Backups and copied DB files must remain read-only/offline. HMAC replay protection is authoritative inside one writable SQLite lineage; a copied DB opened concurrently with the same secret is outside that guarantee. Before promoting a restore or clone, retire the old writer, rotate `TECH_TALENT_OUTREACH_SECRET`, and issue fresh dry-run/authority receipts.

## Boundaries

- Never use `tech-candidate-outreach/scripts/send_outreach.py --send`; that legacy flag is permanently disabled.
- Never invent human approvals, exact `SEND` confirmations, or SMTP credentials.
- Never bypass the canonical `reply-monitor` Skill with direct IMAP code. It owns bounded polling, `needs_review` CAS decisions, UIDVALIDITY reset authorization, and inbox-run recovery.
- `opt_out` and `hard_bounce` create permanent suppression/contact effects. `out_of_office` and `soft_bounce` are non-terminal events and never authorize an automatic follow-up.
