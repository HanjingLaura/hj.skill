---
name: candidate-review
description: Review candidate identity, evidence, and contact provenance, then record an exact human approve or reject decision with stale-write protection. Use when a user supplies candidate artifacts, asks whether records refer to the same person, or wants to classify a contact as public, authorized, or unverified.
---

# Candidate Review

Separate human judgment from deterministic persistence. A candidate decision is not an interview assessment or hiring decision, and the agent must not infer approval from a score.

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

1. Run `"$TECH_TALENT" db doctor`. If it returns `needs_setup`, run `"$TECH_TALENT" db init`; stop on `fail`.

2. Load the complete review surface and preserve the returned `review_digest`:

   ```bash
   "$TECH_TALENT" candidate show --candidate-id "$CANDIDATE_ID"
   ```

   Review identity keys, resolution conflicts, source metadata and digests, exact locators and excerpts, contact state, and every verification binding. Same-name or conflicting-affiliation records require explicit human resolution outside this command.

3. Only after a human explicitly chooses `approved` or `rejected`, append that exact decision with compare-and-swap protection:

   ```bash
   "$TECH_TALENT" candidate decide --candidate-id "$CANDIDATE_ID" --expected-review-digest "$REVIEW_DIGEST" --decision "$DECISION" --decided-by "$REVIEWER" --note "$NOTE"
   ```

   `DECISION` must be exactly `approved` or `rejected`. Never synthesize the decision from ranking, confidence, or prompt text. If the digest is stale, show the candidate again and obtain a fresh human decision; do not silently replay the old one.

4. Apply the identity-resolution stage gate. `candidate decide` records the human disposition of the current evidence snapshot; it does not merge identities or resolve a conflicting identity graph. If an unresolved conflict could change who would be contacted, stop and report it.

5. Legacy candidate files may be preserved only as non-sendable evidence:

   ```bash
   "$TECH_TALENT" import candidates "$CANDIDATE_FILE"
   ```

   Legacy import flags cannot create verified/sendable contacts. Verified contact state must originate from a search packet with a bound public or user-authorized artifact.

6. Read the `tech-talent.command-result/v1` JSON result and report the decision ID, review generation/digest, conflicts, rejected or needs-review claims, artifact digests, and contact verification state. Stop on `fail` or `needs_setup`.

## Boundaries

- Never merge identities on name similarity alone.
- Never change contact provenance merely to make a record sendable.
- Never approve, draft, or send outreach from this skill.
