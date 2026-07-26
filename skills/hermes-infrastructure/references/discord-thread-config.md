# Discord Gateway Threading Debugging — Full Path

Session artifact documenting the exact troubleshooting path for disabling thread creation in a new Discord gateway profile. Useful as a reference when the same issue recurs for any profile.

## Symptom
Bot replies create threads under every user message instead of replying in-channel.

## Diagnostic Commands
```bash
# Check service status
hermes -p <name> gateway status

# Watch live logs for thread events
journalctl --user -u hermes-gateway-<name>.service -f --no-pager

# Inspect current discord config
hermes -p <name> config show | grep -A 20 "^discord:"

# Direct YAML read to see all threading keys
python3 -c "
import yaml, json
with open('/home/adora/.hermes/profiles/<name>/config.yaml') as f:
    cfg = yaml.safe_load(f) or {}
print(json.dumps(cfg.get('discord', {}), indent=2))
"
```

## What We Tried (Dead Ends First)

### Attempt 1: `no_thread_channels: ["*"]`
```bash
hermes -p polinkly config set discord.extra.no_thread_channels '["*"]'
hermes -p polinkly gateway restart
```

**Result:** Still threading. The glob exclusion is checked *after* the threading decision is already made. Doesn't override `auto_thread: true`.

### Attempt 2: Setting only `reply_in_thread` under `extra`
```python
discord_cfg["extra"]["reply_in_thread"] = False
```

**Result:** Did not take effect until `auto_thread` was also disabled.

### The Actual Fix (All Three Needed)
```python
discord_cfg = config.setdefault("discord", {})
discord_cfg["auto_thread"] = False
discord_cfg.setdefault("extra", {})
discord_cfg["extra"]["reply_in_thread"] = False
# no_thread_channels can be left untouched or cleared — it doesn't actually disable threading
```

Then:
```bash
systemctl --user restart hermes-gateway-<name>.service
```

## Config Keys Reference (Discord Adapter)

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `discord.auto_thread` | bool | `true` | Whether the bot's replies auto-create threads. **The master kill-switch for threading.** |
| `discord.extra.reply_in_thread` | bool | (unset, defaults to true in adapter) | Individual reply threading. Must be false alongside `auto_thread: false`. |
| `discord.extra.no_thread_channels` | list[string] | `[]` | Channels to skip threading in *after* threading decisions are evaluated. Does NOT disable threading globally. |
| `discord.thread_require_mention` | bool | `false` | Whether threaded replies require a mention. (Separate — doesn't affect creation.) |
| `discord.require_mention` | bool | (varies) | Whether the bot requires mention to respond at all. (Separate concern.) |
| `discord.free_response_channels` | list[string] | `[]` | Channels where the bot responds without mention. (Separate concern.) |

## Verification Checklist
1. `auto_thread: false` is set ✅
2. `extra.reply_in_thread: false` is set ✅
3. Service restarted ✅
4. Live logs show no `thread_created` events when triggering replies ✅
5. Reply appears as direct channel message ✅

## Common Misconception
Setting `no_thread_channels: ["*"]` should disable threads everywhere. It doesn't. It only excludes channels — the threading decision is made upstream. Always set `auto_thread: false` first, then treat channel exclusion as a secondary filter if needed.

## Commit References
- `36ae95847` — feat(gateway): gate message timestamps behind opt-in (default off)
- `bd7fc8fdc` — feat(gateway): inject stable human-readable message timestamps
- `3ff904c4a` — feat(gateway): inject stable human-readable message timestamps

(These commits show the maintainers' approach: separate stable metadata block for cache efficiency. Same principle applies to threading config — cache-aware design.)
