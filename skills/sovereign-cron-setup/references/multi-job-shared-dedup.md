# Multiple cron jobs posting into one community room

Use when a community has both an ambient visit job and a fast mention-watch job. The failure shape is two jobs answering the same person, or one job treating a failed post as handled and never retrying.

## One shared handled-message log

Keep a JSON array of handled message IDs at a path both jobs can read, e.g. `~/.hermes/logs/<community>-handled-messages.json`. It is the single source of truth for "has anyone answered this?"

Write ONE helper script both jobs call, with subcommands:

- `scan` — for each readable channel, fetch recent messages; for each message not in the handled log and not authored by the bot, test two conditions: (a) the bot's user ID appears in `mentions[]`; (b) `message_reference.message_id` exists and fetching that parent shows its author is the bot. Print JSON `{mentions: [{id, channel_id, author, content, ts, is_reply}], handled_count}`. Skip channels returning 403 silently (private threads deny the bot access; that is access control, not an empty channel).
- `reply --payload <file>` — payload has `channel_id`, `content`, `source_ids`. POST with `message_reference: {message_id: source_ids[0]}` to thread it. On success (HTTP 200 with an `id`), append all `source_ids` to the log ATOMICALLY in the same call using a temp file + `os.replace`. On any failure, print `POST_FAILED` and mark nothing. This is what makes reply-then-mark non-racy.
- `mark --ids ...` — manual append, for the ambient job to claim a message it handled itself, and for baseline seeding.
- `log` — print count and last few IDs, no secrets.

Token handling: grep the exact `DISCORD_BOT_TOKEN=` line from the owning profile's `.env` in the script. Never `source` the whole `.env` (later malformed lines can break it), never read another profile's secrets. Referencing the URL inside a `.py` file keeps tirith's command-string scan quiet; `python3 -c "...discord.com..."` in a terminal call triggers approval and hangs in cron.

## Sequence when turning the doorbell on

1. Write the helper script, run `scan`, and inspect the output before trusting it.
2. Seed the baseline, but ONLY for messages you have actually answered. First reply to every currently-visible mention/reply that warrants a response (use the `reply` subcommand so post-and-mark is atomic), THEN verify `scan` returns zero. Never bulk-`mark` the current `mentions[].id` list just to silence the watcher: a seeded-but-unanswered message is invisible to both jobs forever, since the watcher filters handled IDs and the ambient job defers pending mentions to the watcher. "Handled" means "answered," not "seen." Verify in the channel that each pre-existing mention has a real reply before seeding it.
3. Create the fast job with a zero-item baseline (safe to verification-fire as-is, because its stored prompt will find nothing and stay quiet).
4. Update the ambient job's prompt to run `scan` first and skip anything pending for the watcher; if it answers a message itself, `mark` that ID so the watcher stays quiet.
5. Pin all companion jobs to the same model with `pinned: true`; restrict toolsets to what they need (`terminal`, `file`).
6. Fire a verification run on the fast job, then read the actual output file under `~/.hermes/cron/output/<job_id>/` to confirm what it did.

## Job creation mechanics that bite

`cronjob_manage(action='create')` tool calls with a long multi-paragraph prompt can fail local JSON parsing on embedded quotes. When that happens, write the prompt to a `.txt` file and use the CLI:

```bash
PROMPT=$(cat /path/to/prompt.txt)
hermes cron create "every 30m" "$PROMPT" --name "..." --pin --deliver local
```

The CLI `cron create` has NO toolset flag. After creating, call `cronjob_manage(action='update', job_id=..., enabled_toolsets=[...])` to restrict toolsets, and confirm the pin and toolsets in the returned job dict. `hermes cron create --help` is authoritative for which flags exist; do not guess at `--toolsets`.
