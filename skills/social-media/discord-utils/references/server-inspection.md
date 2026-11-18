# Server Inspection with the Bot Token

Read-only reconnaissance. Use the owning profile's token (the `discord` tool resolves it, or read `DISCORD_BOT_TOKEN` from that profile's own `.env`). Never read another profile's credentials to answer a server question.

## Confirm the bot is actually in a guild

`GET /users/@me/guilds` — compare the guild count and look for the guild id before and after an invite. A channel fetch succeeding is not proof of membership worth reporting; the guild list is. `GET /channels/{cid}` returns `guild_id`, so a channel link resolves to its guild.

## Identify real moderators, not just role names

1. `GET /guilds/{gid}/roles` — decode each role's `permissions` integer. Useful bits: KICK `1<<1`, BAN `1<<2`, ADMIN `1<<3`, MANAGE_GUILD `1<<5`, MANAGE_CHANNELS `1<<13`, MANAGE_MESSAGES `1<<28`. Record role id + name + position for any role with these bits.
2. `GET /guilds/{gid}/members?limit=100` — paginate with `&after=<last member user id>` until a batch is shorter than 100. For each member, intersect `roles[]` with the staff-role ids. Include `owner_id` from `GET /guilds/{gid}`.
3. Report the intersection, not the role list. A role named "Moderator" with no permission bits and no holders is not staff.

## Who is a message responding to

`GET /channels/{cid}/messages` gives each message a `message_reference` dict (`message_id` is the target; `type: 0` is a reply). `mentions[]` is a DIFFERENT thing — a reply can mention nobody, or mention someone other than its target. To answer "who is this replying to," read `message_reference` and resolve that id in the same channel; do not infer from `mentions` or from adjacent messages.

## Linked channel or thread returns 403 Missing Access (50001)

That means this token cannot see the channel. Do not infer its content and do not claim a tool failure. Check `GET /guilds/{gid}/threads/active` — a public thread appears there with its `parent_id`; an id from a link that is absent (or still 403) is private or restricted. Say plainly that you cannot read it, and offer to work from pasted text. Silence about content you cannot verify is the correct outcome.

## Time

Discord `timestamp` fields are UTC. Convert to the user's local zone before saying anything about time of day or who was awake.
