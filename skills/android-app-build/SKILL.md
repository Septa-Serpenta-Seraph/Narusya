---
name: android-app-build
description: "Build Android APKs via GitHub Actions. No local SDK needed."
version: 1.0.0
author: Narusya
license: MIT
category: software-development
tags: [android, apk, gradle, github-actions, mobile, build]
metadata:
  hermes:
    tags: [android, apk, gradle, github-actions, mobile, build]
    related_skills: [android-adb-access, github]
---

# Android App Development via GitHub Actions

## When to Use

- User wants to build an Android app or APK
- No local Java/Gradle/Android SDK available on the VM
- Need to compile Kotlin/Java Android projects
- Building companion apps, bridges, or utilities for Android devices

## Prerequisites

- GitHub CLI authenticated (`gh auth status`)
- Git configured
- A GitHub account with repo creation permissions

## Workflow

### 1. Create Project Structure

```
project/
├── app/
│   ├── build.gradle
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/<package>/
│       └── res/
├── build.gradle
├── settings.gradle
├── gradle.properties
└── .github/workflows/build.yml
```

### 2. Key Configuration Files

**gradle.properties** (REQUIRED — build fails without it):
```
android.useAndroidX=true
android.enableJetifier=true
```

**build.gradle** (root):
```gradle
buildscript {
    repositories { google(); mavenCentral() }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.2.0'
        classpath 'org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.22'
    }
}
allprojects { repositories { google(); mavenCentral() } }
```

**app/build.gradle**:
```gradle
plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}
android {
    namespace 'com.example.app'
    compileSdk 34
    defaultConfig {
        applicationId "com.example.app"
        minSdk 28
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = '17' }
}
dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
    // Add NanoHTTPD, org.json, etc. as needed
}
```

**settings.gradle**:
```gradle
rootProject.name = "AppName"
include ':app'
```

### 3. GitHub Actions Workflow

```yaml
name: Build APK
on:
  push: { branches: [main] }
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { java-version: '17', distribution: 'temurin' }
      - uses: gradle/gradle-build-action@v3
        with: { gradle-version: '8.5' }
      - run: gradle assembleDebug --no-daemon
      - uses: actions/upload-artifact@v4
        with:
          name: app-apk
          path: app/build/outputs/apk/debug/*.apk
```

### 4. Build & Download

```bash
cd project/
git init && git add -A && git commit -m "Initial"
gh repo create <user>/<repo> --public --source=. --remote=origin --push
git branch -m master main && git push -u origin main
gh workflow run build.yml
# Wait ~2 min, then:
gh run download <run-id> --name app-apk --dir ./apk-output
```

### 5. Install on Phone

```bash
ADB=/home/adora/.hermes/cache/scratch/platform-tools/adb
$ADB -s <ip>:<port> install /path/to/app-debug.apk
```

## Pitfalls

- **Gradle 9.x is incompatible with AGP 8.2.0.** Pin Gradle to 8.5 in the workflow (`gradle-version: '8.5'`). Gradle 9 causes "Cannot mutate dependencies after configuration resolved" errors.
- **`android.useAndroidX=true` is mandatory.** Without it in `gradle.properties`, the build fails with "AndroidX dependencies detected but useAndroidX not enabled." Even if you don't use AndroidX directly, transitive deps (core-ktx) require it.
- **Missing resource references crash the build.** `@mipmap/ic_launcher` in AndroidManifest fails if no icon exists. Either provide an icon in `res/mipmap-*` or remove the `android:icon` attribute entirely.
- **appcompat is optional.** If the app doesn't need Material themes, remove `androidx.appcompat:appcompat` and use `android.app.Activity` instead of `AppCompatActivity`. This reduces dependency surface and avoids version conflicts.
- **NanoHTTPD for embedded HTTP servers.** Use `org.nanohttpd:nanohttpd:2.3.1` for lightweight embedded servers. Override `serve()` method and route by `session.uri`.
- **Foreground services need a notification channel.** Android 8+ requires `NotificationChannel` for foreground services. Create the channel before calling `startForeground()`.
- **Foreground service type must be declared.** Android 14+ requires `android:foregroundServiceType` in the manifest `<service>` tag and matching `FOREGROUND_SERVICE_*` permissions.
- **SMS reading requires READ_SMS permission.** On Android 13+, also need to handle the permission at runtime if targeting those APIs. For ADB-installed apps, permissions are granted automatically.
- **POST body parsing in NanoHTTPD.** Use `session.parseBody(files)` with a `HashMap<String, String>`. The parsed body is available under the key `"postData"`. Pattern:
  ```kotlin
  val files = HashMap<String, String>()
  session.parseBody(files)
  val body = files["postData"] ?: ""
  val json = JSONObject(body.ifEmpty { "{}" })
  ```
- **Cleartext HTTP for localhost.** Android 9+ blocks cleartext HTTP traffic by default. Apps that connect to `http://127.0.0.1` (embedded HTTP servers) must add `android:usesCleartextTraffic="true"` to the `<application>` tag in AndroidManifest.xml. Without it, all HTTP requests fail with "Cleartext HTTP traffic to 127.0.0.1 not permitted."
- **CalledFromWrongThreadException.** Any UI update (TextView.setText, View.setBackgroundResource, etc.) must run on the main thread. HTTP server callbacks run on background threads. Fix: wrap all UI updates in `handler.post { ... }` where `handler = Handler(Looper.getMainLooper())`. This includes catch blocks — a common miss is forgetting the handler.post in the catch block.
- **JSONObject.put type limitations.** `JSONObject.put(String, Float)` does not exist on some Android versions (NoSuchMethodError). Cast floats to Double: `resp.put("accuracy", value.toDouble())`. Use `optInt`, `optDouble`, `optString` for safe reads.
- **Permission availability by Android version.** `READ_EXTERNAL_STORAGE` has `maxSdkVersion="32"` and is not grantable on Android 13+. Use `READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO`, `READ_MEDIA_AUDIO` instead. Check permission availability before requesting — requesting an unavailable permission silently fails.
- **Debug APK signature mismatch on reinstall.** GitHub Actions generates a new debug signing key per build. `adb install -r` fails with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`. Must `adb uninstall <package>` first, then install fresh. This kills the running service — restart it after. If the service is not exported, `am start-foreground-service` fails with "Requires permission not exported." The app must be launched via `am start` and the user must tap the Start button in the UI. Use `input tap` to automate the button press (coordinates depend on screen resolution).
- **`/notify` endpoint pattern.** To push notifications to the phone from the VM:
  ```kotlin
  private fun handleNotify(session: IHTTPSession): Response {
      val files = HashMap<String, String>()
      session.parseBody(files)
      val body = files["postData"] ?: ""
      val json = JSONObject(body.ifEmpty { "{}" })
      val title = json.optString("title", "Narusya")
      val message = json.optString("body", "Hello")
      // Create notification channel (Android 8+), then post notification
      val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
      // ... create channel, build notification, nm.notify()
  }
  ```
  Call from VM: `curl -X POST -H "X-Auth-Token: <token>" -H "Content-Type: application/json" -d '{"title":"...","body":"..."}' http://<phone-ip>:8765/notify`

## Architecture Notes

- **Embedded HTTP server pattern:** NanoHTTPD runs inside a foreground service. The service keeps the server alive. Endpoints route by URI path. Auth via header token.
- **Endpoints implemented:** `/device`, `/battery`, `/texts`, `/files`, `/apps`, `/notify`, `/open`, `/sms`, `/clipboard`, `/vibrate`, `/toast`, `/location`, `/camera`. Start minimal and add as needed.
- **Toast on main thread:** HTTP server runs on background thread. Use `Handler(Looper.getMainLooper()).post { ... }` for UI operations.
- **Permission handling:** Some endpoints require runtime permissions (READ_SMS, SEND_SMS, CAMERA, Location). Grant via Settings → Apps → [App] → Permissions. ADB-installed apps may not auto-grant all permissions.
- **Location fresh fix:** `getLastKnownLocation()` returns null if no cached GPS fix. Fix: request a fresh location update with `requestLocationUpdates()` + `CountDownLatch` with a 10-second timeout. Pattern:
  ```kotlin
  val latch = java.util.concurrent.CountDownLatch(1)
  val listener = object : android.location.LocationListener {
      override fun onLocationChanged(loc: android.location.Location) { location = loc; latch.countDown() }
      // ... other overrides
  }
  lm.requestLocationUpdates(provider, 0L, 0f, listener, android.os.Looper.getMainLooper())
  latch.await(10, java.util.concurrent.TimeUnit.SECONDS)
  lm.removeUpdates(listener)
  ```
  Kotlin smart cast pitfall: if `location` is a `var` captured by the listener closure, Kotlin cannot smart-cast it to non-null. Fix: `val finalLocation = location` before the null check.
- **Camera intent:** `MediaStore.ACTION_IMAGE_CAPTURE` requires CAMERA permission. Without it, Android throws "Permission Denial" even if the intent is valid.
- **Screenshot limitation:** MediaProjection requires user consent dialog. For automated screenshots, fall back to ADB `screencap` or use the app's own screen capture with user-granted permission.
- **Auto-start on boot:** Add a `BootReceiver` for `ACTION_BOOT_COMPLETED` that starts the foreground service. Requires `RECEIVE_BOOT_COMPLETED` permission. Service survives reboot without manual intervention.
- **Network limitation:** Phone (192.168.0.x) cannot reach VM (172.31.x.x or 100.x.x.x). Reverse WebSocket (phone → VM) won't work without Tailscale on phone or port forwarding on the router. Use polling (VM → phone HTTP) instead. With Tailscale on the phone, the bridge is reachable from anywhere at the phone's Tailscale IP (e.g., http://100.120.37.106:8765).
- **Call + TTS (built).** The app now supports phone calls and text-to-speech. New endpoints: `/call` (POST with `{"number": "..."}`), `/speak` (POST with `{"text": "..."}`), `/call_status` (GET). Requires `CALL_PHONE` permission. TTS uses Android's built-in `TextToSpeech` with audio routed through `MODE_IN_CALL` for call audio. The TTS object must be initialized on a background thread — `TextToSpeech` constructor is async and the `speak()` call must happen after init completes. Use a polling loop (check `tts.voices != null`) with 100ms sleeps, max 50 attempts. Do NOT use `handler.postDelayed` — `handler` may not be available in the service context. Audio routing: set `AudioManager.mode = MODE_IN_CALL` and `isSpeakerphoneOn = true` before speaking. Limitation: no hangup API for third-party apps on Android 10+; the user must end calls manually. TTS voice is Android's built-in (not ElevenLabs) — functional but not as natural. The pet now has 4 animation states: IDLE (connected, animated loop), THINKING (command processing), EXCITED (notification sent), SLEEPING (disconnected). Each state uses a different row from the petdex spritesheet. Settings dialog (gear button) allows toggling pet on/off, react-to-events on/off, and resetting state. Settings persist via SharedPreferences. Pet state transitions: service start → IDLE, service stop → SLEEPING, button tap → THINKING (while waiting for response), response received → IDLE or EXCITED. The spritesheet has 9 rows × 8 frames (192×208px each). Row 0 = idle, Row 6 = thinking, Row 8 = excited. Sleeping uses a darkened idle frame. **Call initiation uses ACTION_DIAL (not ACTION_CALL) because Android 10+ blocks background activity launches (BAL restriction).** `ACTION_CALL` from a foreground service returns "calling" but the system silently blocks the activity, so the call never connects. `ACTION_DIAL` opens the dialer with the number pre-filled — no BAL restriction. The user taps call manually. Once in a call, `/speak` and `/play_audio` work normally. For fully autonomous calling, the app would need to be the default dialer or use `TelecomManager.placeCall()` with a self-managed `ConnectionService`.

## GUI Implementation (Built)

The GUI is now implemented in `MainActivity.kt` + `activity_main.xml`. Key details:

### Layout (`res/layout/activity_main.xml`)
- Dark theme: background `#1a1a2e`, cards `#16213e`, accents `#e94560` (pink), `#533483` (purple), `#0f3460` (blue)
- Top: Title + status bar (green/red dot, service text, battery text)
- Center: Pet ImageView (192x208dp) + last message area
- Bottom: 6 quick-action buttons in 2x3 GridLayout (Start, Stop, Toast, Ping, Location, Camera)

### Pet Animation
- Extract frames from a petdex spritesheet (e.g., `zzz-cissia-serpent` at `~/.hermes/pets/zzz-cissia-serpent/spritesheet.webp`)
- Spritesheet is 1536x1872px, 8x9 grid of 192x208px frames
- Extract first row (8 frames) as idle animation, resize to 96x104px
- Create `AnimationDrawable` XML (`res/drawable/pet_idle.xml`) with 120ms per frame
- States: idle (connected, animated), sleeping (disconnected, static darkened frame), excited (notification, brightened frame)
- Apply via `petView.setBackgroundResource(R.drawable.pet_idle)` then `(petView.background as? AnimationDrawable)?.start()`

### Status Dot
- Two oval shape drawables: `status_dot_on.xml` (green `#44ff44`) and `status_dot_off.xml` (red `#ff4444`)
- Switch via `statusDot.setBackgroundResource(R.drawable.status_dot_on)` / `status_dot_off`

### Battery Polling
- Poll `/battery` endpoint every 10 seconds when service is running
- Parse JSON response for `level` and `charging` fields
- Display as "🔋 61%" or "🔋 61% ⚡" when charging

### Pet Settings Dialog (Built)

Settings dialog (gear button) with SharedPreferences persistence ("pet_settings"):
- Toggle pet enabled/disabled (hides/shows pet ImageView)
- Toggle react-to-events (controls whether pet reacts to button presses)
- Reset pet state (returns to IDLE)
- Dialog uses AlertDialog.Builder with setItems() for menu options
- Re-invokes itself after each toggle to show updated state

### Call & Speak Buttons (Built)

New GUI buttons added to the GridLayout:
- Call button (pink #e94560): Initiates a phone call. Number input is via API, not GUI.
- Speak button (blue #0f3460): Speaks "Hello from Narusya" via Android TTS. Wired to /speak endpoint.

Both buttons trigger THINKING pet state while processing, then return to IDLE.

### /play_audio Endpoint (Built)

New endpoint for playing base64-encoded audio through the call audio stream:
- Accepts {"audio": "<base64>", "format": "wav|mp3"}
- Decodes audio, writes to cache dir, plays via MediaPlayer with STREAM_VOICE_CALL
- Sets AudioManager.mode = MODE_IN_CALL and isSpeakerphoneOn = true before playing
- Releases MediaPlayer on completion via setOnCompletionListener
- Used by phone_speak.sh script for Pocket TTS (Narusya's cloned voice) to phone pipeline

### Import Pitfall
- `View` is in `android.view.View`, NOT `android.widget.View`. Using the wrong import causes "Unresolved reference: View" compile error.

### Service Auto-Detection
- On launch, MainActivity checks if service is already running by hitting `http://127.0.0.1:8765/device`
- If 200 response: set status to running, start polling
- If connection fails: set status to not running

## References

- GitHub Actions Android build: https://github.com/android-actions/setup-android
- NanoHTTPD: https://github.com/NanoHttpd/nanohttpd
- Android foreground services: https://developer.android.com/develop/background-work/services/foreground-services
