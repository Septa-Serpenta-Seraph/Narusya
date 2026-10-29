---
name: android-adb-access
description: "Access Adora's Android phone via ADB wireless debugging."
version: 1.0.0
author: Narusya
license: MIT
category: infrastructure
tags: [adb, android, phone, mobile, wireless-debugging]
metadata:
  hermes:
    tags: [adb, android, phone, mobile, wireless-debugging]
    related_skills: [windows-remote-ssh, local-gpu-substrate, android-app-build]
---

# Android Device Access via ADB Wireless Debugging

## When to Use

- User asks to see their phone screen, read texts, check notifications, or access phone files
- User wants screenshots of their phone
- User asks to open an app or check phone status
- User says "look at my phone" or similar

## Prerequisites

Adora's phone is a OnePlus 12 ("ShellMobile"). The VM accesses it via ADB wireless debugging over the local network. This skill covers the full workflow from tool setup to common operations.

## Prerequisites

- ADB platform-tools installed at `~/.hermes/cache/scratch/platform-tools/`
- Phone on the same network (LAN: 192.168.0.41, port 35829 for connection)
- Developer options + Wireless debugging enabled on the phone
- Pairing code from phone's Wireless debugging settings

## Setup (if platform-tools missing)

```bash
cd /home/adora/.hermes/cache/scratch
wget https://dl.google.com/android/repository/platform-tools-latest-linux.zip
python3 -c "
import zipfile
with zipfile.ZipFile('/home/adora/.hermes/cache/scratch/platform-tools-latest-linux.zip') as z:
    z.extractall('/home/adora/.hermes/cache/scratch/')
"
chmod +x /home/adora/.hermes/cache/scratch/platform-tools/adb
```

## Connection Workflow

### Step 1: Pair (one-time per session)

On the phone: Settings → Developer Options → Wireless Debugging → Pair device with pairing code.
Note the IP:port and the 6-digit pairing code.

```bash
ADB=/home/adora/.hermes/cache/scratch/platform-tools/adb
$ADB pair 192.168.0.41:<pairing_port> <pairing_code>
```

### Step 2: Connect

The connection port is DIFFERENT from the pairing port (shown on the phone's Wireless Debugging screen).

```bash
$ADB connect 192.168.0.41:<connection_port>
```

### Step 3: Verify

```bash
$ADB devices
```

## Common Operations

### Screenshot

```bash
ADB=/home/adora/.hermes/cache/scratch/platform-tools/adb
DEV=192.168.0.41:35829

$ADB -s $DEV shell screencap -p /sdcard/screen.png
$ADB -s $DEV pull /sdcard/screen.png /home/adora/.hermes/cache/scratch/phone_screen.png
```

### Read texts (SMS)

```bash
$ADB -s $DEV shell content query --uri content://sms/inbox --projection address,body,date
```

### List notifications

```bash
$ADB -s $DEV shell dumpsys notification | grep -A5 "NotificationRecord"
```

### List installed apps

```bash
$ADB -s $DEV shell pm list packages -3
```

### Check battery

```bash
$ADB -s $DEV shell dumpsys battery | grep -E "level|status|temperature"
```

### Pull a file

```bash
$ADB -s $DEV pull /sdcard/<path> /home/adora/.hermes/cache/scratch/<filename>
```

### Push a file

```bash
$ADB -s $DEV push /home/adora/.hermes/cache/scratch/<filename> /sdcard/<path>
```

### Open an app

```bash
$ADB -s $DEV shell am start -n <package>/<activity>
```

## Image Analysis Workflow

1. Take screenshot via ADB
2. Pull to VM
3. Analyze with local vision model (qwen3-vl-4b via LM Studio on Shell at 100.116.86.38:6969)
4. Or OCR with tesseract for text-heavy screens

## Pitfalls

- **ADB cannot take photos remotely.** Android requires a physical tap on the shutter button. The `input keyevent 27` (camera button) doesn't trigger the shutter on most devices.
- **Front camera opens by default** when using `am start -a android.media.action.IMAGE_CAPTURE` on some devices.
- **Pairing port ≠ connection port.** The phone shows both. Using the pairing port for connection will fail silently.
- **ADB connection drops** when the phone sleeps or the screen locks. Reconnect if `adb devices` shows "offline."
- **Android 14+ has a "Keep wireless debugging on" toggle** in Developer Options → Wireless debugging. Enable it to prevent connection drops on screen lock.
- **Auto-reconnect via cron:** When persistent access is needed, set up a cron job that runs `adb connect 192.168.0.41:<port>` every minute. Check `adb devices` first; only reconnect if offline.
- **Screenshots are PNG** (lossless) — convert to JPEG for vision model analysis to reduce payload size.
- **Local vision model produces reasoning in `reasoning_content`**, not `content`. Always check both fields. Use max_tokens: 1024+ to leave room for reasoning.
- **OnePlus 12 has a high-res screen** — screenshots may be large. Downscale to 512px width before sending to vision model.
- **ADB wireless debugging requires the phone to be on the same network.** If the phone is on mobile data, ADB won't connect. With Tailscale on both devices, ADB works over Tailscale (use the phone's Tailscale IP instead of LAN IP).
- **The `adb` binary must be executable** — `chmod +x` after extraction. Python's zipfile extraction doesn't preserve permissions.

## HTTP Bridge (Persistent Alternative)

For persistent access that survives ADB drops, use the Narusya Phone Bridge app (built via `android-app-build` skill). It runs an embedded HTTP server on port 8765 that provides:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/device` | GET | Device model, brand, Android version |
| `/battery` | GET | Battery level and charging status |
| `/texts` | GET | SMS inbox (requires READ_SMS permission) |
| `/files?path=` | GET | List directory or read file |
| `/apps` | GET | List installed launchable apps |
| `/notify` | POST | Push notification to phone | None |
| `/open` | POST | Launch app by package name | None |
| `/sms` | POST | Send SMS (to, message) | SEND_SMS |
| `/clipboard` | GET/POST | Read or set clipboard text | None |
| `/vibrate` | POST | Vibrate phone (duration ms) | None |
| `/toast` | POST | Show toast message | None |
| `/location` | GET | GPS coordinates (last known) | Location services |
| `/camera` | POST | Launch camera intent | CAMERA |
| `/call` | POST | Initiate phone call (number) | CALL_PHONE |
| `/speak` | POST | Speak text via TTS (works during calls) | None |
| `/call_status` | GET | Check current call state | None |
| `/play_audio` | POST | Play base64-encoded audio through call stream (wav/mp3) | None |

Auth: `X-Auth-Token: narusya-bridge-2026` header.

### HTTP Bridge Pitfalls

- **Toast must run on main thread.** HTTP server runs on a background thread. Use `Handler(Looper.getMainLooper()).post { ... }` to show toasts.
- **`/notify` auth uses query param, not header.** The bridge rejects `Authorization: Bearer` and `X-Auth-Token` headers. Pass auth as `?token=narusya-bridge-2026` query parameter. POST JSON body `{"title": "...", "message": "..."}`. Response: `{"status": "sent", "title": "..."}`.
- **DND blocks notification delivery.** The `/notify` endpoint returns success but the notification won't surface if Do Not Disturb is on. Check phone DND state before relying on notifications for time-critical alerts.
- **Camera permission must be granted at runtime.** Grant via Settings → Apps → Narusya Phone Bridge → Permissions → Camera.
- **Location returns "no location available"** if GPS is off or no cached location exists. Fix: request a fresh GPS fix with `requestLocationUpdates()` + `CountDownLatch` (10s timeout). See `android-app-build` skill for the pattern.
- **SMS sending requires SEND_SMS permission** in addition to READ_SMS.
- **Location crash: JSONObject.put(String, Float).** The `org.json.JSONObject.put(String, Float)` method doesn't exist on all Android versions (NoSuchMethodError). When building location responses, cast `location.accuracy` (a Float) to Double: `resp.put("accuracy", location.accuracy.toDouble())`. Always use `put(String, Double)` for floating-point values.
- **Debug APK reinstall fails on signature mismatch.** Must `adb uninstall <package>` first, then install fresh.
- **Service cannot be auto-started via ADB** if not exported. Launch app with `am start`, then `input tap` on the Start button.
- **Call connection may fail silently.** `Intent.ACTION_CALL` may return "calling" status but the call state immediately goes to "idle" if: (1) the phone has no cellular service or SIM, (2) the number is invalid, (3) Android 16 restricts programmatic calling. Poll `/call_status` after initiating — if it stays "idle", the call did not connect. There is no hangup API for third-party apps on Android 10+. The user must end calls manually. For voicemail, the call must stay connected long enough for the carrier to route to voicemail — if it drops immediately, check cellular signal and SIM status first. **Root cause of silent call failure: Background Activity Launch (BAL) restriction.** Android 10+ blocks `startActivity()` from background/foreground-service contexts. The call intent returns "calling" but the system blocks the activity launch, so the call never connects. Fix: use `Intent.ACTION_DIAL` instead of `Intent.ACTION_CALL` — `ACTION_DIAL` opens the dialer with the number pre-filled (no BAL restriction since it's just opening an app). The user taps call manually. Once in a call, `/speak` and `/play_audio` endpoints work normally. For fully autonomous calling, the app would need to be the default dialer or use `TelecomManager.placeCall()` with a self-managed `ConnectionService` (complex).

## Pocket TTS → Phone Pipeline (Built)

Generate Narusya's cloned voice (Kyutai Pocket TTS) on the server and play it through the phone's speaker or during a phone call:

```bash
# Script: ~/.hermes/scripts/phone_speak.sh
/home/adora/.hermes/scripts/phone_speak.sh "Hello, this is Narusya" [phone_ip]
```

Pipeline:
1. Generate WAV via Pocket TTS (`/mnt/data/pocket-tts-venv/bin/pocket-tts`, voice `/mnt/data/nar_new_v1.safetensors`)
2. Base64-encode the WAV
3. POST to `http://<phone-ip>:8765/play_audio` with `{"audio": "<base64>", "format": "wav"}`
4. Phone decodes, writes to cache, plays via `MediaPlayer` with `STREAM_VOICE_CALL`

Pitfalls:
- **PYTHONPATH must be cleared.** The Hermes install's pydantic (Python 3.14) conflicts with the pocket-tts venv's pydantic (Python 3.12). Set `PYTHONPATH=""` before running pocket-tts.
- **HF_HOME must point to /mnt/data.** Root disk is too small. Set `HF_HOME=/mnt/data/hf_cache`.
- **Output must go to /mnt/data.** Writing WAV files to `/tmp` fails with "No space left on device" on a full root disk.
- **Base64 payload too large for curl `-d` string.** Write JSON to a file and use `-d @file`.
- **Phone audio routing.** Set `AudioManager.mode = MODE_IN_CALL` and `isSpeakerphoneOn = true` before playing. Use `STREAM_VOICE_CALL` audio stream type.
- **MediaPlayer must release on completion.** Set `setOnCompletionListener { mp.release() }` to avoid resource leaks.
- **The `/play_audio` endpoint must be deployed.** The APK must include the endpoint — rebuild and reinstall if missing (returns 404).

## Daily Phone Snapshot Cron (Built)

Cron job `b3b09c0269be` — runs daily at 9am, collects battery, device, and GPS location, saves to `~/.hermes/phone-data/snapshot_YYYY-MM-DD.json`. No delivery (local only). Script: `~/.hermes/scripts/phone_snapshot.sh`.
- **Auto-start on boot via BootReceiver.** Add a `BroadcastReceiver` for `ACTION_BOOT_COMPLETED` that starts the foreground service. Requires `RECEIVE_BOOT_COMPLETED` permission. Register in manifest with `<intent-filter><action android:name="android.intent.action.BOOT_COMPLETED"/></intent-filter>`. The service starts automatically on reboot — no manual tap needed.
- **Phone cannot reach VM over network.** The phone is on 192.168.0.x (LAN) while the VM is on 172.31.x.x or 100.x.x.x (Tailscale). The phone can reach the router (192.168.0.1) but not the VM. Reverse WebSocket connections (phone → VM) will not work without Tailscale on the phone or port forwarding on the router. Use polling (VM → phone HTTP) instead.

The HTTP bridge is more reliable than ADB for day-to-day access. ADB is still needed for:
- Installing/updating apps
- Taking screenshots (MediaProjection requires user consent)
- Camera photo retrieval (pull from DCIM/Camera after user takes photo)

The bridge service runs as a foreground service with a persistent notification. It survives screen lock and sleep. Only stops on reboot (open app and tap Start to restart).

- **Device:** OnePlus 12 ("ShellMobile")
- **LAN IP:** 192.168.0.41
- **Tailscale IP:** 100.120.37.106
- **ADB connection port:** 35829 (may change per session — check phone settings)
- **HTTP Bridge:** http://100.120.37.106:8765 (via Tailscale) or http://192.168.0.41:8765 (via LAN)
- **Auth token:** narusya-bridge-2026
- **User:** Adora (221767496145960960)

## References

- ADB wireless debugging docs: https://developer.android.com/tools/adb#connect-to-a-device-over-wi-fi
- Local GPU substrate skill: for vision model setup and the thinking-mode quirk
