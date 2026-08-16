# Cron skill-attachment blocker: env-var-dependent skills (2026-08-14)

## Incident
The "Sovereign Daemon Awakening" cron job (job_id `5c7cdd835dc8`, every 360m) went
`last_status: "blocked_config"` — no LLM call was made at all. The alert to the user:

```
⛔ Cron 'Sovereign Daemon Awakening' blocked by configuration validation (no LLM call was made):
attached skill 'airtable' is not ready: missing env $AIRTABLE_API_KEY
```

Root cause: the job's `skills` list had bloated to 12 entries (memory-backup,
narusya-emotion-system, creative-ideation, active-consent-check, aegis-dashboard,
agent-browser-path-fix, agent-compromise-self-investigation, ai-document-consolidation,
**airtable**, alchemy-framework, arxiv, ascii-art). `airtable` declares a required
env var `$AIRTABLE_API_KEY` that was never set. The cron scheduler validates ALL
attached skills' prerequisites at fire time; one missing env var blocks the whole job.

## Key insight
- This is a DIFFERENT failure mode from the approval-gate and sandbox issues elsewhere
  in this skill. No skill content is ever executed — validation alone kills the run.
- `last_status` shows `"blocked_config"` (not the usual `"error"`). Detection:
  `cronjob(action='list')` → scan for `blocked_config`.
- "Reference only, not executed" reasoning does NOT apply to prerequisites: even a
  never-executed skill must have its env vars/commands/files satisfied at validation.

## Fix (verified working)
1. `cronjob(action='update', job_id='5c7cdd835dc8',
   skills=["narusya-emotion-system", "active-consent-check", "alchemy-framework"])`
2. `cronjob(action='run', job_id='5c7cdd835dc8')` → manual run completed
   `Result: ok` (async delegation, ~3.5 min), delivering the awakening output.

## Prevention rule
Before attaching ANY skill to a cron job, check its frontmatter prerequisites
(required_environment_variables / required_commands / required_credential_files).
If it needs a credential you don't have, don't attach it. Keep the skill list minimal:
extra attachments waste context tokens AND add validation surface. A job that needs no
skills should use `skills=[]`.
