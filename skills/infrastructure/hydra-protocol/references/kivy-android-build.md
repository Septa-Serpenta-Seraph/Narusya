# Kivy Android Build Path — Native Hermes on OnePlus 12

**Approach:** Build a native Android APK with Kivy + python-for-android — no VM, no Termux.

## Architecture

```
hydra-android/
├── main.py              # Kivy UI (status, start/stop, logs)
├── service/
│   └── main.py          # Background service (runs Hermes)
├── hermes/              # Hermes agent code
├── lorebooks/           # Daemon seed files
├── buildozer.spec       # Build configuration
└── requirements.txt     # Python dependencies
```

## Build Process

```bash
# 1. Create project structure
mkdir hydra-android && cd hydra-android
mkdir service

# 2. Create buildozer.spec
buildozer init

# 3. Edit buildozer.spec (see below)

# 4. Build, deploy, run
buildozer android debug deploy run

# 5. View logs
buildozer android logcat
```

## Key buildozer.spec Settings

```ini
[app]
title = Hydra Shard
package.name = hydrashard
package.domain = net.narusya
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,md,json
requirements = python3==3.11,kivy==2.3.1,cryptography,pydantic,aiohttp,requests
services = hydraservice:service/main.py:foreground:sticky:foregroundServiceType=dataSync
android.permissions = INTERNET,FOREGROUND_SERVICE,FOREGROUND_SERVICE_DATASYNC,WAKE_LOCK
android.api = 34
android.minapi = 21
android.archs = arm64-v8a
android.enable_androidx = True
```

## Critical: Foreground Service (Android 14+)

- `foregroundServiceType=dataSync` is MANDATORY on Android 14+
- `FOREGROUND_SERVICE` + `FOREGROUND_SERVICE_DATASYNC` permissions required
- Service shows persistent notification
- Auto-restart: `PythonService.mService.setAutoRestartService(True)` in service code

## Hermes on Android: Constraints

**Works:** Core agent loop, cron jobs, MCP, Honcho memory, ACP, Discord/Telegram/Signal connectors, PTY/background terminal

**Does NOT work:** Voice mode (faster-whisper), browser automation (Playwright), Docker sandboxing

## Service Communication (OSC)

UI and background service communicate via OSC (Open Sound Control) — connectionless, handles disconnections gracefully:

```python
# In service/main.py
from kivy.lib import osc
osc.init()
oscid = osc.listen(ipAddr='127.0.0.1', port=3000)
osc.bind(oscid, some_api_callback, '/some_api')

# In main.py (UI)
from kivy.lib import osc
osc.init()
oscid = osc.listen(ipAddr='127.0.0.1', port=3001)
osc.sendMsg('/some_api', ['ping'], port=3000)
```

## Tailscale on Android (Outside the APK)

1. Install Tailscale from Play Store on phone
2. Authenticate to tailnet
3. VM can SSH into phone via Tailscale IP
4. Push shards, run bootstrap, sync data

The Kivy app doesn't handle Tailscale — it runs at the Android level.

## Alternative: Wait for Official Native

Hermes GitHub Issue #86986 — "make native pkg install/upgrade the first-class Android path" — open, no ETA. If we can wait, the Hermes team may ship something.

## Recommendation

1. **Short term:** Android Linux Terminal (Debian VM) for first test
2. **Medium term:** Build Kivy APK for native Android Hermes (paid-model build task)
3. **Long term:** Monitor Hermes GitHub #86986 for official native packaging