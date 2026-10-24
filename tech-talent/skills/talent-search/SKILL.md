---
name: talent-search
description: Prepare bounded technical-candidate discovery and import reviewed schema v1 artifacts. Use when a user asks to find candidates by role, school, repository, paper, or research direction, or to register an existing candidate Markdown, CSV, or JSONL file.
---

# Talent Search

Use public evidence and the deterministic local Core. Never treat search-engine snippets as identity or contact proof.

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

## Workflow

1. Run the local readiness check and read its JSON result:

   ```bash
   "$TECH_TALENT" db doctor
   ```

   If the result is `needs_setup`, run `"$TECH_TALENT" db init` and repeat doctor. Stop on `fail`.

2. Apply the search stage gate. Codex may use its available public search capabilities to collect a bounded offline packet; the Core itself performs no network calls. Fix the scope before discovery, including channels, queries, and hard budgets. Never claim exhaustive coverage.

3. Produce strict UTF-8 JSON/JSONL plus local UTF-8 artifacts. Search packet V1 accepts only `frontier_result`, `search_hit`, `source_artifact`, and `candidate_claim` events. Every artifact event must bind its exact lowercase SHA-256 and byte count. Snippets are discovery hints only; public or user-authorized artifact excerpts are required for trusted identity/contact claims.

4. Validate and atomically ingest the packet:

   ```bash
   "$TECH_TALENT" search ingest --scope "$SCOPE_JSON" --packet "$PACKET_JSONL" --artifact-root "$ARTIFACT_DIR" --receipt "$RECEIPT_JSON"
   ```

   Exit `0` means complete coverage under the declared scope; exit `3` means a truthful partial result. Stop on exit `1` or `2`. Never relabel partial as complete because candidates were found.

5. Inspect the persisted run when needed:

   ```bash
   "$TECH_TALENT" search show --run-id "$RUN_ID"
   ```

   Report `status`, `run_id`, scope/packet digests, query/page coverage, rate limits/timeouts, dedupe counts, identity conflicts, and verified-contact counts from `tech-talent.command-result/v1`.

## Boundaries

- Use only public pages, public APIs, repositories, papers, and user-authorized local exports.
- Do not log in to recruiting platforms, bypass access controls, guess a sendable email, or claim exhaustive web coverage.
- Do not draft or send outreach from this skill.
