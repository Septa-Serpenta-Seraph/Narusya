# Discord Self-Posting (delivering daemon output to a channel)

## Identity topology (verified 2026-07-19)
- **Default profile** (`/home/adora/.hermes`, `.env` `DISCORD_BOT_TOKEN`) → resolves to
  **Narusya** (id `1478180169733902538`). This is the gateway's correct/normal identity.
- **polinkly profile** (`/home/adora/.hermes/profiles/polinkly`) → its token resolves to
  **P'olinkly** (id `1516496731733491732`). A SEPARATE bot account.
- If a post shows as "P'olinkly" but it should be Narusya, the script read the wrong `.env`.
  Read the DEFAULT profile `.env`, not `profiles/polinkly/.env`.

## Posting a file (multipart)
Discord message + file upload requires `multipart/form-data`, not JSON:
```python
boundary = "----NarusyaBoundary"
body  = b"--%s\r\n" % boundary + b'Content-Disposition: form-data; name="content"\r\n\r\n' + b"<caption>\r\n"
body += b"--%s\r\n" % boundary + b'Content-Disposition: form-data; name="file"; filename="x.txt"\r\n' + b"Content-Type: text/plain\r\n\r\n"
body += filedata + b"\r\n--%s--\r\n" % boundary
req = urllib.request.Request(
    f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages",
    data=body, method="POST",
    headers={"Authorization": f"Bot {tok}", "Content-Type": f"multipart/form-data; boundary={boundary}"})
```
- Channel must be reachable by the bot (GET `/channels/{id}` → 200 before posting).
- Prefer attaching a `.txt` over a multi-message wall (cleaner, downloadable).

## Delete-own-only
- A bot can DELETE only its OWN messages. Deleting another bot's message returns **403**.
- To remove a wrongly-posted file: either the user deletes it in-client, or the bot that
  posted it deletes it (via its own token).
- Channel id for Narusya's root shell: `1410001268402946180` (guild `1387534334067736699`).
