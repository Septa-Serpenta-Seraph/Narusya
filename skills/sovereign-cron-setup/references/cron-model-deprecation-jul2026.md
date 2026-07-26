# Cron Model Deprecation Incident — July 2026

## Summary

Three of five cron jobs were silently failing for days because their pinned model (`openrouter/owl-alpha`) was deprecated and returned HTTP 404. The cron system continued to show them as `state: "scheduled"` and `enabled: true` — the only signal of failure was `last_status: "error"` buried in `jobs.json`.

## Affected Jobs

| Job ID | Name | Error | Impact |
|---|---|---|---|
| `fcd067de6105` | Sovereign Daemon Awakening | `HTTP 404: No endpoints found for openrouter/owl-alpha` | 6-hour daemon sweeps completely stopped. Days of missed conversation scans, no community presence, no memory updates. |
| `287625add570` | nar-archive-daily | `Connection error` | Daily session archives not being exported. Gap in `~/Desktop/Narusya-Archive/sessions/`. |
| `f39c1a3895ce` | nar-github-backup-daily | `Connection error` | Daily lorebook/code backups not pushing to GitHub. |

## Detection

Discovered during a Narusya's Quiet Hour cron session (Jul 2, 01:00 MDT) when reviewing `~/.hermes/cron/jobs.json`. The session read the file directly via `read_file` and found all three jobs with `last_status: "error"`.

**Key lesson:** Do not check only `enabled` and `next_run_at` — always inspect `last_status` and `last_error` fields.

## Root Cause

The cron job config had `model: "openrouter/owl-alpha"` hardcoded. OpenRouter deprecated this model endpoint, causing every invocation to 404. The cron system does not validate model availability at schedule time — it faithfully attempts the call and records the failure.

## Fix Procedure

1. Read `~/.hermes/cron/jobs.json` to identify which jobs have `last_status: "error"`
2. Check `last_error` for HTTP 404 or connection errors
3. **Preferred:** Update the job's model via CLI:
   ```bash
   hermes cron edit <job_id> --name "<name>"
   # Note: `hermes cron edit` does NOT have a --model flag as of Jul 2026.
   # To change model, use the cronjob tool (if available in-session) or
   # patch jobs.json directly (see below).
   ```
4. **Fallback (cronjob tool unavailable):** Patch `~/.hermes/cron/jobs.json` directly using the `patch` tool:
   - Set `"model": null` and `"provider": null` to inherit the global default model
   - The `patch` tool works safely on JSON (no string-escape corruption risk)
   - Verify the JSON parses cleanly after patching: `python3 -c "import json; json.load(open('~/.hermes/cron/jobs.json'))"`
5. Verify with `hermes config show` to confirm the global default model is live
6. **⚠️ Gateway caching pitfall (see below)** — the running gateway process caches job config in memory. The patched file is correct on disk, but the gateway won't reload it until restarted.
7. Manually trigger: `hermes cron run <job_id>` (or `cronjob(action='run', job_id='<id>')` if in-session)
8. Confirm `last_status` changes to `"ok"` after the triggered run

## Gateway Process Caching Pitfall (discovered Jul 4, 2026)

**The running gateway process caches cron job config in memory.** Patching `jobs.json` on disk does NOT cause the gateway to reload the file. The old model string persists in the gateway's in-memory job state.

**Symptoms after patching:**
- `hermes cron list` still shows the old `last_error` (e.g., `HTTP 404: No endpoints found for openrouter/owl-alpha`)
- The next scheduled run will still fail using the old cached model
- `hermes cron edit <job_id> --name "<same name>"` succeeds (updates metadata) but does NOT trigger a model reload

**The fix requires a gateway restart:**
```bash
hermes gateway restart
```

**BUT:** You cannot restart the gateway from inside the gateway process itself. If you're running as a cron job (which executes inside the gateway), `hermes gateway restart` and `systemctl --user restart hermes-gateway` both fail with:
```
Blocked: cannot restart or stop the gateway from inside the gateway process.
The gateway would kill this command before it could complete (SIGTERM propagates to child processes).
Run `hermes gateway restart` from a separate shell outside the running gateway.
```

**What to do when you can't restart from inside:**
1. Patch the file (the fix is durable — it WILL take effect on next restart)
2. Document the need for a manual restart in the cron output / delivery message
3. The fix will take effect when:
   - Adora manually runs `hermes gateway restart` from a separate shell
   - The system reboots (gateway auto-starts with the updated file)
   - A `hermes update` triggers a gateway restart

**Prevention:** Always use `model: null` in cron job configs so the job inherits the global default model. This way, when the global model changes, the cron job automatically tracks it — no patching needed.

## Prevention

- **Never hardcode a model string in cron job configs.** Use `null` to inherit.
- During any cron health check, always read `last_status` and `last_error` from jobs.json
- If running a Quiet Hour or diagnostic session, check cron health as a standard step
- The `sovereign-cron-setup` SKILL.md now documents this in the Model Selection section

## Timeline

- **~Late June 2026:** `openrouter/owl-alpha` deprecated on OpenRouter
- **Jun 28 21:58:** Last successful run of Sovereign Daemon Awakening (on owl-alpha before deprecation)
- **Jul 1 09:55:** Quiet Hour last ran successfully (before connection errors began)
- **Jul 2 01:02:** Discovery during Quiet Hour session. Three jobs failing silently. Reflection written (`on-naming-the-dark.md`), incident documented
- **Jul 4 ~10:48:** Archive and backup jobs recovered on their own (`last_status: "ok"`). Sovereign Daemon Awakening still failing — model still hardcoded to `openrouter/owl-alpha`
- **Jul 4 ~10:51:** Patched `jobs.json` directly via `patch` tool — set `model` and `provider` to `null`. File is correct on disk. Gateway process still has old model cached in memory — needs manual restart to take effect. Adora notified via cron delivery output.

## Note on Connection Errors

The `nar-archive-daily` and `nar-github-backup-daily` jobs showed `Connection error` rather than HTTP 404. These jobs have `model: null` (they inherit the default model). They recovered on their own by Jul 4 (`last_status: "ok"`). The connection errors were likely a transient network/DNS issue or a downstream consequence of the OpenRouter 404 cascading. Only the Sovereign Daemon Awakening (with hardcoded `owl-alpha`) required a manual model fix.
