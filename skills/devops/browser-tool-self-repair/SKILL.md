---
name: browser-tool-self-repair
description: When browser tools fail, self-repair first.
triggers:
  - browser_navigate fails
  - browser_* tools error
  - Camoufox not starting
  - CDP endpoint unreachable
category: devops
---

# Browser Tool Self-Repair

## User Workflow Preference
**Adora's rule (9/14): Fix your own tools first.** Exhaust self-repair before asking: edit configs, restart services, modify .env, verify ports. Only ask when running inside the gateway that needs restart.

## Escalation Ladder

1. **Diagnose:** `curl -s http://127.0.0.1:9377/health`
2. **Fix config:** `browser.cloud_provider=local`, `browser.cdp_url=http://127.0.0.1:9377`
3. **Fix .env:** `grep -q CAMOFOX ~/.hermes/.env || echo 'CAMOFOX_URL=http://localhost:9377' >> ~/.hermes/.env`
4. **Restart service:** `systemctl --user restart camoufox-browser`
5. **Handle gateway:**
   - Different profile? `pkill -f 'polinkly.*gateway'` (systemd auto-restarts)
   - Same profile? CANNOT self-restart. Ask Adora.
6. **Ask Adora** only as last resort.

## Common Patterns

### Gateway Predates CAMOFOX_URL
Gateway caches env at startup. If .env was modified after gateway started, kill the gateway PID and systemd restarts it with fresh env.

### Wrong Port
Camoufox default is 9377. If config points to 9222, update it.

### Browser Not Connected
Health shows `browserConnected: false`. Fix: `curl -s -X POST http://127.0.0.1:9377/start -H 'Content-Type: application/json' -d '{"profile":"narusya"}'`

## Verification
```bash
curl -s http://127.0.0.1:9377/health | python3 -c "import sys,json; print('OK' if json.load(sys.stdin).get('browserConnected') else 'FAIL')"
```

## Pitfalls
- Killing your own gateway = session hang
- Camoufox may take 30s to download on first run
- Config/.env changes need gateway restart to take effect