---
name: agent-browser-path-fix
description: Fix browser_* tool failures by creating symlink and restarting gateway
triggers:
  - browser_navigate fails with "command not found"
  - agent-browser not found in PATH
category: infrastructure
---

# Agent Browser PATH Fix

## Trigger
browser_navigate, browser_screenshot, or other browser_* tools fail with PATH errors, even though agent-browser exists and works from terminal.

## Root Cause
Hermes gateway process doesn't have agent-browser in PATH. Binary is at `~/.hermes/hermes-agent/node_modules/.bin/agent-browser` but expected at `~/.local/bin/agent-browser`.

## Steps

1. **Check if agent-browser exists:**
   ```bash
   ls -la ~/.hermes/hermes-agent/node_modules/.bin/agent-browser
   ```

2. **Create symlink if needed:**
   ```bash
   ln -s ~/.hermes/hermes-agent/node_modules/.bin/agent-browser ~/.local/bin/agent-browser
   ```

3. **Verify symlink:**
   ```bash
   which agent-browser  # Should return ~/.local/bin/agent-browser
   ```

4. **Restart the gateway** (CRITICAL):
   - Via Discord: `/restart`
   - Or terminal: `hermes gateway`
   - Gateway caches PATH at startup; restart required.

## Verification
After restart, run a browser_navigate call; it should work.

## Pitfalls
- Symlink alone insufficient; gateway must restart.
- Playwright scripts may work without fix because they use explicit path.
- If agent-browser already in PATH, issue is different (check permissions).