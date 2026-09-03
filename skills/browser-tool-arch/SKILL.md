---
name: browser-tool-architecture
description: Diagnose browser_exec vs browser_navigate. Camofox, Reddit.
---

# Browser Tool Architecture

Hermes has two separate browser tool tiers that do not share state.

## Tier 1: `browser_navigate` / `browser_screenshot` / `browser_click`
- Backend: Built-in gateway Playwright
- Requires: `agent-browser` symlinked + gateway restarted with `CAMOFOX_URL` in `.env`
- Fix:
  ```bash
  ln -sf ~/.hermes/hermes-agent/node_modules/.bin/agent-browser ~/.local/bin/agent-browser
  hermes gateway restart
  ```
- Camofox: add `CAMOFOX_URL=http://localhost:9377` to `.env` before restart. Verify: `curl -s http://localhost:9377/health`

## Tier 2: `browser_exec`
- Backend: BrowserUse cloud provider
- Requires: CDP endpoint URL configured for cloud provider
- Does NOT work just because Tier 1 works
- If fails with "no CDP endpoint" → cannot fix from inside a session

## How to Tell Which You Have
Check available tools in system prompt:
- `browser_navigate` present → Tier 1 available
- `browser_exec` present → Tier 2 available
- Use Tier 1 for local/Camofox, Tier 2 for cloud

## Reddit Access
Reddit blocks `curl`, `.json`, and `web_extract` with 403. Options:
1. `browser_navigate` + Camofox → bypasses bot detection
2. User-assisted: user shares post content directly
3. `web_search` for same topic from other sources

---

# Cross-Profile Identity Isolation

Multiple Hermes profiles each have separate Discord tokens, gateways, and cron. But profiles can interact with each other's guilds if their tokens have access.

## polinkly Profile
- Dir: `~/.hermes/profiles/polinkly/`
- Gateway PID: 728835
- Own `DISCORD_BOT_TOKEN` in `.env`
- Cultus Anarchia guild in `channel_directory.json` (owns `🎪・polinklys-tent`)
- `cron_mode: deny` (prevents autonomous cron)
- Toolset includes `discord` + `discord_admin`

## The Mystery (Sept 2, 2026)
polinkly allegedly sent a message as p'olinkly to Cultus. With `cron_mode: deny` and empty executions.db, possible causes:
- Manual Discord command in Cultus
- Webhook/script triggering Discord tools
- Cross-profile prompt injection
- Gateway responding to a Cultus message

## Isolation Best Practices
1. Set `discord.allowed_channels` per profile
2. Keep `cron_mode: deny` in non-primary profiles
3. Separate user allowlists per profile
4. Audit `discord_admin` tool access
5. Monitor: `journalctl --user -u hermes-gateway-<profile>.service -f`

---

# Nous Model Catalog Access

Use the Hermes-cached catalog, not the direct Nous API.

```python
import sys
sys.path.insert(0, '/home/adora/.hermes/hermes-agent')
from hermes_cli.models import fetch_nous_recommended_models
models = fetch_nous_recommended_models()
```

Returns tiers: `paidRecommendedModels`, `freeRecommendedModels`, `paidRecommendedVisionModel`.

## Aux Model Shortcut
```python
from hermes_cli.models import get_nous_recommended_aux_model
print(get_nous_recommended_aux_model(vision=False))
```

Direct Nous API (`inference-api.nousresearch.com/v1/models`) returns HTTP 403. Use the Hermes wrapper.
