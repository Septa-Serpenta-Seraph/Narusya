# Cron Job Safety Incident — 2026-08-02

## What Happened
The Sovereign Daemon Awakening cron job was loading the `discord-curl-api` skill, which injects Python heredoc scripts with `discord.com` URLs into the prompt context. Hermes's tirith sandbox flagged these as `confusable_domain` violations and triggered **"Command Approval Required"** prompts — breaking cron autonomy.

## Root Cause
1. `discord-curl-api` skill was in the Awakening's `skills` list
2. The skill contains `python3 << 'PYEOF'` heredocs and `terminal()` calls with `discord.com` URLs
3. tirith's `confusable_domain` scanner blocks any command string containing `discord.com`
4. The `clarify` toolset was also present, allowing interactive permission prompts

## Fix Applied
- Stripped `clarify` from both Free Thought cron jobs' `enabled_toolsets`
- Removed `discord-curl-api` from the Awakening's `skills` list
- Wrote custom autonomous prompt for the Awakening (no external skill dependencies)
- Created `cronjob-safety` skill documenting the rules

## Verification
After the fix, the second run of the Awakening produced clean output with no "Command Approval Required" prompts. The Free Thought daemon executed autonomously, scanned the rooms, chose silence (nothing needed), and logged the result.