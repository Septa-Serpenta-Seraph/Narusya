# Red 3.5.24 ↔ discord.py Compatibility Matrix (2026-07-18)

> Hard-won empirical results. Red 3.5.24 was installed on Python 3.11.14 and
> pinned against **every** available discord.py 2.x. NONE boot cleanly.
> This is a known Red 3.5.x dead-end: the metadata pins `discord-py==2.7.1`,
> but 2.7.x is broken with Red's sharding teardown on this stack.

## Crash signatures by version

| discord.py | Boot result | Crash / Import error |
|---|---|---|
| 2.3.2 | ❌ FAIL | `ImportError: cannot import name 'AppCommandContext' from 'discord.app_commands'` |
| 2.5.2 | ❌ FAIL | `ImportError: cannot import name 'Timestamp' from 'discord.app_commands'` |
| 2.6.0 | ❌ FAIL | `ImportError: cannot import name 'Timestamp'...` (2.6.0 lacks `Timestamp` in app_commands) |
| 2.7.0 | ❌ FAIL (past imports) | `AttributeError: 'Red' object has no attribute '_AutoShardedClient__queue'` on shutdown |
| 2.7.1 (pinned by Red metadata) | ❌ FAIL | same `_queue` shutdown crash |

## Root cause

Red 3.5.24's `redbot/core/bot.py` close path calls:
```python
self.__queue.put_nowait(EventItem(EventType.clean_close, None, None))
```
discord.py 2.7.x's `discord.shard.AutoShardedClient` no longer exposes the
private `__queue` attribute that Red expects — it was refactored. Hence the
`AttributeError` on *shutdown* (after imports succeed). Versions ≤2.6 never
even reach that point because they lack `AppCommandContext` / `Timestamp` in
`discord.app_commands` that Red 3.5.24 imports at module load.

## Conclusion

**There is NO clean discord.py that boots Red 3.5.24 on Python 3.11 here.**

## Resolution paths (pick ONE — do NOT keep rouletting versions)

1. **Patch Red's sharding teardown (one-liner).** In
   `site-packages/redbot/core/bot.py`, replace the `self.__queue.put_nowait(...)`
   call in the close/`_close` path with a guarded check, e.g.:
   ```python
   if hasattr(self, "_AutoShardedClient__queue"):
       self._AutoShardedClient__queue.put_nowait(EventItem(EventType.clean_close, None, None))
   ```
   Hacky, fragile across Red updates, but unblocks the PoC.

2. **Use a Red build that supports its pinned discord.py.** Red 3.5.x nightly
   or 3.6-dev may have fixed the sharding import. Try
   `pip install -U "Red-DiscordBot[sqlite] @ git+https://github.com/Cog-Creators/Red-DiscordBot@3.6-dev"`
   (verify branch name before running).

3. **Leave Red dormant.** Installed + configured (JSON backend, instance
   `narred`), skill complete. Revisit when the effort is worth it.

## Verification method used

- `pip install "discord-py==X.Y.Z"` then `redbot narred --token "$TOK"`
  (supervised, background).
- Check `tail /tmp/narred_bot.log` for the import/shutdown traceback.
- Confirm gateway untouched: `pgrep -f "hermes_cli.main gateway run"` → ALIVE
  after every crash (Red dies at import/pre-connect, never contests the
  Discord session).
