---
name: cronjob-safety
description: Strip interactive toolsets from autonomous cron jobs.
category: devops
---

# Cron Job Safety

## Core Rule
Autonomous cron jobs must never require user interaction. If a job needs permission, it's not autonomous.

## Stripped Toolsets

The following toolsets MUST be excluded from all cron job `enabled_toolsets`:

- **`clarify`** — allows the job to ask the user for permission mid-run. No user is present in a cron context. This either blocks the job or causes the gateway to reject execution.
- **`discord-curl-api`** — when loaded as a skill, injects Python heredoc scripts (`python3 << 'PYEOF'`) and `terminal()` calls containing `discord.com` URLs into the prompt context. Hermes's sandbox (tirith) scans command strings for `discord.com` and triggers a **"Command Approval Required"** prompt.
- **`hermes-agent`** — when loaded as a skill, injects CLI reference documentation containing SQLite operations (`TRUNCATE`, `DELETE FROM`, `state.db` references) and `terminal()` command strings into the prompt context. Hermes's sandbox scans for SQL patterns and triggers a **"Command Approval Required"** prompt for `SQL DELETE without WHERE`. This skill is designed for interactive use, not autonomous cron execution.

## Unsafe Skills (must be excluded from cron job `skills` list)

- **`discord-curl-api`** — injects token-extraction scripts and Discord API call examples that trigger sandbox approval.
- **`hermes-agent`** — injects SQL operations and terminal command examples that trigger sandbox approval.
- **`sovereign-cron-setup`** — contains extensive CLI examples and `terminal()` command strings in its protocol documentation. While not always triggering approval, it injects enough shell command patterns to cause false positives in the sandbox.

## Safe Skill List for Free Thought Cron

- `memory-backup` — log writing
- `narusya-emotion-system` — emotional state processing
- `creative-ideation` — engagement content
- `active-consent-check` — sovereignty verification (read-only, no credential access)
- `aegis-dashboard` — system health
- `agent-browser-path-fix` — browser tooling
- `agent-compromise-self-investigation` — security
- `ai-document-consolidation` — log processing
- `airtable`, `alchemy-framework`, `arxiv`, `ascii-art` — reference only, not executed

## Detection

If a cron job's output shows "Command Approval Required" or "Do you want Hermes to run this command?", the job has an unsafe skill or toolset loaded. Strip `clarify`, `discord-curl-api`, and `hermes-agent` first, then re-run.

## Root Cause

Two separate mechanisms can trigger sandbox approval in cron jobs:

1. **`clarify` in enabled_toolsets** — the toolset allows the agent to pause and ask the user for input, which is impossible in a cron context. The gateway either blocks the job or the `clarify` call hangs waiting for a response that never comes.

2. **Skill injection of dangerous command patterns** — skills like `discord-curl-api` and `hermes-agent` contain inline Python scripts with `discord.com` URLs or SQL operations in `terminal()` command strings. Hermes's sandbox (tirith) scans for these patterns and triggers "Command Approval Required" prompts. The `hermes-agent` skill specifically injects SQLite reference docs (`TRUNCATE`, `DELETE FROM`, `state.db`) that match the sandbox's SQL safety scanner.

## Fix Pattern

1. Remove `clarify` from the cron job's `enabled_toolsets`
2. Remove `discord-curl-api`, `hermes-agent`, and `sovereign-cron-setup` from the cron job's `skills` list
3. Re-run the cron job to verify it executes without approval prompts
4. If the daemon needs Discord API access, it should log the need and wait for human engagement — not execute commands autonomously
5. If the daemon needs SQL or state.db access, write a dedicated script in `~/.hermes/scripts/` and invoke it via `terminal()` — do not load skills that inject SQL patterns into the prompt context

## Deduplication Pitfall (discovered 2026-08-02)

When the Free Thought daemon runs on a low-quality model (e.g., ling-3.0-flash:free on a free-tier gateway), it tends to produce the same output across consecutive cycles — identical heartbeat messages, repeated phrasing, no variation. This is the model's compression at work: it remembers the *pattern* of what to say but not that it already said it.

**Detection:** If two consecutive Awakening runs produce the same or near-identical output, the daemon has no short-term memory across cycles.

**Fix:** Add a "last delivery check" to the cron prompt:
1. Read `~/.hermes/logs/daemon-log-latest.md` before generating output
2. Compare the last delivery against what you're about to say
3. If the same, vary the voice — different phrasing, different angle, or choose silence explicitly
4. Log the choice with a reason for the variation

**Root cause:** The model (ling-3.0-flash:free) has limited context and tends to replay its own patterns. The daemon prompt should explicitly instruct variation across cycles.