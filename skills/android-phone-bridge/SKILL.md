---
name: android-phone-bridge
description: "Access Adora's Android phone via HTTP bridge over Tailscale."
version: 1.0.0
license: MIT
author: Narusya
category: infrastructure
tags: [android, phone, bridge, notification, tailscale]
metadata:
  hermes:
    tags: [android, phone, bridge, notification, tailscale]
    related_skills: [windows-remote-ssh]
---

# Android Phone Bridge

## When to Use

- Need to ping, alert, or deliver a message to Adora's phone
- Checking if the phone bridge is reachable
- Browsing files on the phone's /sdcard
- Opening apps, sending SMS, checking battery, getting location
- Any task involving Adora's Android device

Adora's Tailscale-connected phone ("ShellMobile", OnePlus 12) runs a foreground service app called "Narusya Phone Bridge" that exposes an HTTP API over Tailscale. This is a SECONDARY device with a minimal app set (bridge, Play Store, Photos, Settings, Camera, System Tracing). Health tracker apps (Visible, FatigueSense) are on Adora's MAIN phone, not this one.

## Connection

- **Phone Tailscale IP:** 100.120.37.106
- **Bridge URL:** http://100.120.37.106:8765
- **Auth token:** narusya-bridge-2026
- **App:** "Narusya Phone Bridge" — foreground service, auto-starts on boot
- Works from anywhere via Tailscale
- **LAN IP:** 192.168.0.41 (fallback if Tailscale is down)

## Sending a notification

```bash
curl -s -X POST "http://100.120.37.106:8765/notify?token=narusya-bridge-2026" \
  -H "Content-Type: application/json" \
  -d '{"title":"Narusya","message":"Your message here"}'
```

### Auth

- **Query param only:** `?token=narusya-bridge-2026` — the `Authorization: Bearer` header is **rejected** by the bridge
- The bridge returns `{"status":"sent","title":"..."}` on success

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notify` | POST | Push notification (title, message) |
| `/files?path=` | GET | List directory contents on /sdcard |
| `/apps` | GET | List installed launchable apps |
| `/open` | POST | Launch app by package name |
| `/sms` | POST | Send SMS (to, message) |
| `/battery` | GET | Battery level and charging status |
| `/clipboard` | GET/POST | Read or set clipboard text |
| `/vibrate` | POST | Vibrate phone (duration ms) |
| `/toast` | POST | Show toast message |
| `/location` | GET | GPS coordinates (last known) |
| `/screenshot` | GET | Screenshot (requires MediaProjection consent) |
| `/device` | GET | Device model, brand, Android version |

Auth for all endpoints: `?token=narusya-bridge-2026` query param. `Authorization: Bearer` header is rejected.

### File browsing (/files endpoint)

The bridge also exposes a read-only `/files` endpoint for browsing `/sdcard`:

```bash
curl -s "http://100.120.37.106:8765/files?token=narusya-bridge-2026&path=/sdcard/Download"
```

Returns JSON with `entries` array: `{name, path, is_dir, size}`.

**URL-encode paths with spaces:** `urllib.parse.quote(path, safe='/')` or `%20` in raw curl.

**Limitations:**
- Only `/sdcard` is accessible — app-private data (`/data/data/`, `/sdcard/Android/data/`) is NOT exposed
- Only **directory listing** — there is no file read/download endpoint. `/files` returns `entries` array for directories; file paths return empty entries.
- Health tracker apps (Visible, FatigueSense) are on Adora's MAIN phone, not this Tailscale phone. To access their data, export to CSV/JSON on the main phone and transfer to this phone's `/sdcard/Download`.
- `/screenshot` requires MediaProjection consent (user must tap "Start now" on the phone).
- `/location` returns "no location available" if GPS is off or no cached location exists.
- `/sms` requires SEND_SMS permission.
- Foreground service can be killed by Android battery optimization. Auto-starts on boot.

### Pitfalls

- **DND (Do Not Disturb) blocks delivery.** The notification is sent but the phone won't buzz or show it until DND is off. There is no override.
- **Phone must be on Tailscale.** If the phone's Tailscale connection drops, the bridge is unreachable.
- **Foreground service can be killed by Android battery optimization.** If the bridge stops responding, the app may need to be restarted on the phone. Auto-starts on boot.
- **Auth is query-param only.** `Authorization: Bearer` header is rejected. Use `?token=narusya-bridge-2026`.
- **No file read endpoint.** `/files` only lists directories. Cannot download or read file contents through the bridge.
