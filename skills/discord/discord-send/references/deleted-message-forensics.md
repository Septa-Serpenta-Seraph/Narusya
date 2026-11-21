# Deleted-message forensics and transcript recovery on Discord

Use when asked whether channel history was wiped, when a conversation must be
reconstructed after deletion, or when an archive has to be saved and delivered.

## 1. Prove the deletion

- Keep IDs of messages seen earlier in the session: gateway triggers carry
  `message_id`/`reply_to_id`, and the session's own posts are in state.db.
- `GET /channels/{cid}/messages/{mid}` with the bot token:
  - `200` → still present.
  - `404 {"code": 10008, "message": "Unknown Message"}` → deleted, or a bad ID.
    Require several hits across one window before calling it a wipe.
  - `403` → no access to that channel, NOT evidence of deletion.
- Fetch a window: `GET /channels/{cid}/messages?limit=100`. Newest-first, so reverse
  before reading. A jump between two consecutive timestamps is the deletion window.
- Convert any snowflake to UTC without another API call:
  `datetime.fromtimestamp(((int(mid) >> 22) + 1420070400000)/1000, timezone.utc)`.
  This gives exact boundaries even when the messages themselves are gone.

## 2. Attribute cautiously

- `GET /guilds/{gid}/audit-logs?action_type=72` (MESSAGE_DELETE) or `73`
  (MESSAGE_BULK_DELETE). Bots usually lack VIEW_AUDIT_LOG → `403 Missing Permissions`.
- With no audit entry, report "cannot attribute" and state the permission limit.
  Who was active in the thread, or who wrote the channel rules, is not evidence.

## 3. Recover the text

- `gateway.log` is not a full transcript: it logs inbound messages from the
  configured user only (grep `inbound message`). Other participants are absent.
- Full remembered text lives in `~/.hermes/state.db`:
  1. `select id, chat_id, chat_type, session_key, display_name from sessions
     where chat_id=?` → session id.
  2. `select timestamp, role, content, platform_message_id from messages
     where session_id=? order by timestamp` → trigger text and posts.
- Pitfall: `messages.session_id` holds session IDs (e.g. `20261120_...`), not chat
  IDs. `where session_id like '%{cid}%'` returns zero rows; resolve the session first.
- Trigger `content` embeds `[Recent channel messages]` and `[Context around the
  replied-to message]` blocks containing other participants' lines as they were seen
  at the time. That is the recoverable copy of third-party deleted messages.
- Attachments, and timestamps for messages never seen in a trigger, cannot be
  recovered. Say so plainly instead of reconstructing them.

## 4. Resolve the DM channel

- `GET /users/@me/channels` may return `200` without the target DM. Do not conclude
  it does not exist.
- Find it in `state.db`: `sessions` where `chat_type='dm'` and `display_name` matches
  the person; take `chat_id`.
- Confirm with `GET /channels/{id}` → `type: 1` and the expected `recipients[].username`.

## 5. Deliver and verify

- For Adora, write archives as `.md` and attach them:
  `python3 /home/adora/.hermes/scripts/discord_send.py post {dm_id} "short note" --file /path/archive.md`
  Keep a short plain-text note as the CLI argument; keep markdown in the file so bash
  never has to interpolate it.
- Verify the side effect: `GET /channels/{dm_id}/messages/{sent_id}` and check
  `content`, `attachments[0].filename`, and `size` before saying it landed.
- Discord attachment URLs from the API carry signed `ex`/`is`/`hm` params and expire;
  `web_extract` can read a PDF attachment URL directly while it is fresh.
- When the question is whether a deletion was allowed, read the channel's rules
  messages *and* any PDF attachment (the PDF can be the fuller version) before
  answering; distinguish a "delete walls of text" rule from any authorization to
  wipe a topic or purge a time window.
