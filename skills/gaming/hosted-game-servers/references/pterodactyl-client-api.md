# Pterodactyl Client API Cookbook (PebbleHost-proven)

All requests to `https://panel.<host>/api/client`. Headers:
```
Authorization: Bearer ptlc_...
Accept: Application/vnd.pterodactyl.v1+json
Content-Type: application/json
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
```
**The User-Agent header is mandatory** — without a browser-like UA, Cloudflare returns HTML 403 pages instead of JSON.

Helper pattern: a small `ptero.py` on the agent machine reading the key from the secrets file (key, SID, headers as module constants; an `api(path, method, body)` wrapper that returns `(status, parsed_or_raw)` — parse JSON but fall back to raw text for non-JSON responses like file contents).

## Endpoints
- `GET /` — list servers. Each entry: `attributes.identifier` (8-char server ID used everywhere), `name`, `limits`, `sftp_details`, `feature_limits` (backup slot count!).
- `GET /servers/{id}/resources` — state (running/offline), memory/cpu. State here is the process state, NOT network reachability.
- `POST /servers/{id}/power` — body `{"signal": "start|stop|restart|kill"}` → 204. Restart after config/plugin changes.
- `GET /servers/{id}/files/list?directory=/plugins` — directory listing.
- `GET /servers/{id}/files/contents?file=%2Fserver.properties` — raw file text. Paths are URL-encoded (`%2F` for leading slash).
- `POST /servers/{id}/files/write?file=%2Fserver.properties` — body form is host-dependent (verified 2026-09-29, PebbleHost): plain raw text now returns **403 Forbidden**; PebbleHost accepts a JSON envelope `Content-Type: application/json` + body `{"raw": "<full file text>"}` → 204. If a raw write 403s, retry as the `raw` envelope before assuming a permissions problem. After ANY write, read the file back and verify the change actually landed (one session saw the write API mangle the whole file into a quoted escaped single-line blob — only recovered by re-parsing and rewriting).
- `GET /servers/{id}/files/upload` → signed URL. Append `&directory=/plugins` (or `?directory=/`), then POST multipart with field name `files`. Large jars (60MB) work fine.
- `POST /servers/{id}/files/delete` — body `{"root": "/plugins", "files": ["old.jar"]}`.
- `POST /servers/{id}/command` — body `{"command": "whitelist add Name"}` → 204. Console only; the response lands in `logs/latest.log`, so sleep ~6-10s then read the log.
- `GET /servers/{id}/files/contents?file=%2Fwhitelist.json` — verify whitelist entries (name+uuid).
- `POST /servers/{id}/backups` — start a backup. `GET /servers/{id}/backups` — list (check `is_successful`, `bytes`). **Budget plans cap manual backups (Pebble = 2).** `DELETE /servers/{id}/backups/{backup_id}` returns 204 but the slot may stay occupied — don't fight it.
- `GET /servers/{id}/startup` — list egg variables (JARFILE, LOADER_JAVAVERSION, LOADER_AUTOREBOOT...).
- `PUT /servers/{id}/startup/variable` — body `{"key": "JARFILE", "value": "paper-26.2-129.jar"}` (POST is 405 — it's PUT).
- `GET /servers/{id}/network/allocations` — the public IP:port.
- `GET /servers/{id}/files/contents?file=%2Flogs%2Flatest.log` — boot log; look for 'Done (Xs)!', plugin enable lines, stack traces. Rotated logs are .gz under `/logs`.
- `POST /servers/{id}/command` with `fawe reload` — reloads FAWE config (worldedit-config.yml, config.yml) **live, no restart** → console logs `Configuration reloaded!`. Use after any FAWE config tweak so online players aren't booted (verified 2026-09-29: navigation-wand max-distance change picked up immediately).

## FAWE config quick-reference (SFCA/PebbleHost, 2026-09-29)
`plugins/FastAsyncWorldEdit/worldedit-config.yml` holds the per-player behavior knobs:
- `navigation-wand: item: minecraft:compass, max-distance: <blocks>` — compass `/jumpto`/`/thru` range (default 100). Raised to 1000 live for long-range navigation; no ceiling in FAWE, pick a sane multiple.
- `no-op-permissions: false` is the NORMAL value (means standard WE permission model applies, ops bypass) — don't 'fix' it.
- limits (max-radius, max-blocks-changed, max-brush-radius) default permissive; `disallowed-blocks` list is cosmetic-safety (wheat/fire/redstone_wire).
- `use-inventory.enable: false` = edits draw from creative inventory, not the player's — leave off for creative builders.
Write flow for this file: read full contents → string-replace the one knob → write back via the `raw` JSON envelope → read back to verify → `fawe reload` via console. Never upload a hand-rebuilt full YAML.

## Console-log diagnostics
- `whitelist add <name>` on a nonexistent username logs `That player does not exist` but returns 204 — always check the log + whitelist.json.
- Plugin 'enabled' ≠ healthy: EssentialsX on an unsupported server version logs an ERROR 'unsupported server version' but still fully functions — judge by subsequent INFO lines, not the ERROR alone.

## External verification (do not trust panel state alone)
- TCP: `bash -c 'echo > /dev/tcp/<ip>/<port>'` — connect/refused in one line.
- Status ping: `https://api.mcsrvstat.us/3/<ip>:<port>` — online, version, MOTD, players (cache ~5 min).
- A server wedged after a backup + restart sequence can show 'running' in the panel while refusing connections — a full restart re-binds the port.

## Automated backups pattern
Panel scheduled-task 'backup' is NOT in the valid action enum (only command/power). Instead run a cron on the agent's own machine: script does (1) resources check → start if stopped, (2) `save-all flush` console command, (3) POST backups, (4) sleep 60, GET backups, report name/size/is_successful. Deliver results to a home channel via cron job.

## Auth preflight (2026-10-01 finding — silent backup-net outage)
Cron backup jobs can fail for a full cycle with an error that looks nothing like the panel: `No access token found for Nous Portal login` at the *auth preflight* stage, not the panel call. Diagnosis chain: (1) check `~/.hermes/auth.json` — look for `last_auth_error.code: invalid_grant` ("refresh token was already rejected; please re-authenticate") and `credential_pool.<provider>: []` (access token cleared when refresh failed); (2) the trap: a `.env` key for the same provider can still exist and be a genuine-looking JWT, yet the preflight validator blocks because `active_provider` points at the dead pool entry. Fix is a re-login for that provider (`hermes auth login <provider>`) — do NOT trigger interactive logins autonomously; report the root cause + exact fix command to the user. Also: crons that gate on these checks may spend their whole run diagnosing instead of delivering — a cron that must always deliver should read preflight state cheaply and bail loudly, not deep-dive.
