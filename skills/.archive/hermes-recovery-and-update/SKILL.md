---
name: hermes-recovery-and-update
description: Recover Hermes after power outage or system restart (Hyper-V setups), and fix config resets after hermes update. Covers gateway service installation, headless access via dummy HDMI, and post-update config restoration.
category: devops
triggers:
  - "power outage recovery"
  - "hermes update"
  - "gateway not running"
  - "config reset after update"
  - "geekom recovery"
  - "cron runs at wrong time"
  - "timezone mismatch"
  - "VM is on UTC"
---

# Hermes Recovery & Post-Update Config Fix

## Power Outage Recovery (Hyper-V + Ubuntu VM)

### Boot sequence (what to wait for)
1. Windows host boots — Geekom powers on automatically
2. Hyper-V starts — VM may auto-start if configured
3. Ubuntu VM boots — 30-60 seconds after Hyper-V
4. Services start — Anydesk, Tailscale, Hermes gateway

Total recovery time: 3-5 minutes. Don't panic if things aren't immediately available.

### Recovery checklist
```bash
# Check if VM is running (from Windows host)
# Open Hyper-V Manager, check VM status
# If stopped: right-click VM, Start

# Check if gateway is running (from Ubuntu terminal)
hermes gateway status

# If gateway not running:
hermes gateway start
# Or if service not installed:
hermes gateway install
hermes gateway start
```

### Anydesk accept session after power outage
If Anydesk asks for remote side to accept:
- Unattended access may have been reset after power loss
- Need physical monitor temporarily to click Accept
- Dummy HDMI plug (5 dollars, Amazon) keeps display active without a real monitor
- Plug into second HDMI port while real monitor is connected, then remove real monitor
- Then enable Anydesk unattended access: Settings, Security, Unattended Access, enable and set password

### Gateway service installation (one-time)
```bash
# Install as user service (survives logout)
hermes gateway install

# Verify linger is enabled (survives reboots)
loginctl show-user $USER | grep Linger

# If linger not enabled:
loginctl enable-linger $USER
```

## Post-Update Config Reset

hermes update resets some config values to defaults. After every update, check these in config.yaml:

### 1. Compression re-enabled
Change compression.enabled from true to false

### 2. Summary model reset to Gemini
Change summary_model from google/gemini-3-flash-preview to your preferred model
Also check auxiliary.compression.model

### 3. Personality reset to kawaii
Change display.personality from kawaii to default

### 4. Other settings that may reset
- human_delay.mode may re-enable
- tts voice settings
- stt provider and model settings
- Any custom toolsets configuration

### Prevention before updating
Save your current config before running hermes update, then diff after to see what changed.

## Merge Conflicts During Update

If hermes update shows a merge conflict (usually in package-lock.json):
1. Say Y to reset working tree to clean state
2. Stashed changes are preserved, nothing is lost
3. The conflict is in dependency files, not your config

## Model ID Format (OpenRouter)

Common mistake: using slashes instead of hyphens.
```
# WRONG: anthropic/claude/sonnet-4.6
# RIGHT: anthropic/claude-sonnet-4.6
```

Valid OpenRouter Anthropic models:
- anthropic/claude-opus-4.6
- anthropic/claude-sonnet-4.6
- anthropic/claude-sonnet-4.5
- anthropic/claude-sonnet-4
