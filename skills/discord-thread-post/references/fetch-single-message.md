# Fetching a single Discord message by ID (via channel windowing, verified 2026-09-26)

The `discord` tool's `fetch_messages` action has no 'get one message by id'
mode, but it accepts optional `before`/`after` snowflake filters. To read a
specific message (e.g. Adora links `discord.com/channels/G/chanID/msgID` and
asks 'what is this?'):

1. `fetch_messages(channel_id, before=<msgID>, limit=2)` — returns the anchor
   message itself (before-N includes the message just before the cut, so the
   last item in the list is msgID minus one; do BOTH calls and you have it).
2. `fetch_messages(channel_id, after=<msgID>, limit=2)` — returns messages
   AFTER it including nearby context.

Calling with BOTH before and after narrows the window tightly around the
anchor. Attachment objects (with `cdn.discordapp.com` URLs incl. expiring
`ex=/is=/hm=` params) work directly in vision_analyze's image_url.

Verified case: msgID `1553276831841517628` in the SFCA builds channel —
windowing recovered it (a reddit link Tyler shared) plus its conversational
context (Rob's datapack discussion).