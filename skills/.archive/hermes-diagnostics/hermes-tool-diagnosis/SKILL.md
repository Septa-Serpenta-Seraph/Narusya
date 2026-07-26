---
name: hermes-tool-diagnosis
category: hermes-diagnostics
description: Diagnose why Hermes tools (browser, voice, etc.) fail when they work in terminal.
triggers:
  - tool calls returning errors
  - "tools not working"
  - "browser broken"
  - terminal commands work but tool calls don't
---

# Hermes Tool Diagnosis

When a Hermes tool (browser_*, voice, etc.) fails but the underlying CLI works from terminal, the issue is usually PATH environment mismatch between the gateway process and the shell.

## Steps

### 1. Identify the failing tool's binary
Check what the tool actually calls:
```bash
grep -r "agent-browser\|SUBPROCESS\|spawn\|exec" ~/.hermes/hermes-agent/src/tools/ | head -20
```

### 2. Test from terminal vs gateway
```bash
# Does it work in shell?
which agent-browser 2>/dev/null || echo "NOT IN PATH"
command -v agent-browser

# Check gateway's environment
ps aux | grep hermes-gateway
cat /proc/$(pgrep -f hermes-gateway | head -1)/environ | tr '\0' '\n' | grep PATH
```

### 3. Common fixes

**PATH mismatch:** Gateway started before tool was installed
```bash
# Check where binary actually lives
find ~/.hermes -name "agent-browser" -type f 2>/dev/null
# Create symlink to standard PATH location
ln -sf ~/.hermes/hermes-agent/node_modules/.bin/agent-browser ~/.local/bin/agent-browser
# Gateway needs restart to pick up new PATH
```

**Stale sockets/lock files:**
```bash
ls /tmp/agent-browser-* 2>/dev/null
# Remove stale browser socket directories (safe - these are temp files)
# WARNING: Only removes directories starting with /tmp/agent-browser-
find /tmp -maxdepth 1 -type d -name 'agent-browser-*' -exec rm -rf {} + 2>/dev/null
```

**Permission issues:**
```bash
ls -la ~/.hermes/secrets/
chmod 600 ~/.hermes/secrets/*.enc
```

### 4. Verify fix
```bash
# Test from gateway's perspective
env -i PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin" agent-browser --help
```

### 5. Restart gateway
Fix won't take effect until gateway restarts (caches PATH at startup):
```bash
# Via hermes CLI or /restart in Discord
hermes gateway restart
```

## Pitfalls
- Symlink fix alone won't work — gateway MUST restart
- Playwright scripts using `npx playwright-core` bypass this entirely (useful workaround)
- Check both `browser_start` errors AND `browser_screenshot` errors (different failure modes)
