# Spotify Integration Setup

Set up Spotify in Hermes from scratch: plugin install, toolset enable, dev app creation, OAuth login, and remote SSH tunneling.

## When to use
- User wants to connect their Spotify account to Hermes for the first time.
- Spotify tools are not available or login has expired.
- Setting up on a remote VM where the browser can't reach localhost directly.

## Prerequisites
- Hermes Agent (>=0.21.6)
- A Spotify account (Free or Premium)
- Access to Spotify Developer Dashboard (https://developer.spotify.com/dashboard)
- SSH access to the VM if Hermes runs remotely

## Setup Steps

### 1. Install and enable the plugin
```bash
hermes plugins install spotify
hermes tools enable spotify
```
Note: `hermes plugins enable spotify` may fail with uv/git errors due to disk space. If so, manually set in config.yaml:
- `plugins.enabled`: add `spotify`
- `plugins.disabled`: remove `spotify`
- `known_plugin_toolsets.cli`: ensure `spotify` is listed

### 2. Create Spotify Developer App
1. Go to https://developer.spotify.com/dashboard
2. Click **Create app**
3. App name: anything (e.g., "Nar Bridge")
4. App description: anything
5. **Redirect URI** (critical): `http://127.0.0.1:43827/spotify/callback`
   - HTTP is permitted on loopback IP literals (Spotify's redirect URI rules)
   - If dashboard refuses http://, use `https://127.0.0.1:43827/spotify/callback` and set `HERMES_SPOTIFY_REDIRECT_URI` env var
   - Paste without trailing space (field rejects with "This redirect URI is not secure")
6. Check **Web API**
7. Agree to terms, create app
8. Copy the **Client ID**

### 3. Login (local machine)
```bash
hermes spotify login --client-id <CLIENT_ID>
```
The command opens a browser for OAuth approval. Tokens saved to `auth.json` under `providers.spotify`.

### 4. Login (remote VM via SSH)
When Hermes runs on a VM and the user's browser is on a different machine:

1. User opens SSH tunnel from their machine:
   ```bash
   ssh -L 43827:127.0.0.1:43827 <user>@<vm-ip>
   ```
2. Run login with --no-browser:
   ```bash
   hermes spotify login --client-id <CLIENT_ID> --no-browser
   ```
3. Give the user the authorization URL from the output
4. User opens URL in browser (tunnel carries callback to VM)
5. Login completes when callback is received

### 5. Verify
```bash
hermes spotify status
```
Should show `spotify: logged in` with auth_type `oauth_pkce`.

## Pitfalls
- **Redirect URI mismatch**: The most common failure. The URI in the Spotify app must EXACTLY match `http://127.0.0.1:43827/spotify/callback` (no trailing slash, no https unless configured).
- **Port forwarding**: On remote setups, the SSH tunnel must be active during the entire OAuth flow. If the tunnel drops, the callback fails silently.
- **Port conflict**: If a previous login attempt left port 43827 in use, the next attempt fails with "Address already in use." Kill the stale process: `fuser -k 43827/tcp` (or `lsof -ti:43827 | xargs kill`), then retry.
- **Top tracks/artists require `user-top-read` scope**: The default login scopes do NOT include `user-top-read`. Without it, `/me/top/tracks` and `/me/top/artists` return 403. Re-login with `--scope "user-top-read user-read-recently-played playlist-read-private playlist-read-collaborative user-modify-playback-state user-library-read user-library-modify playlist-modify-private playlist-modify-public user-read-playback-state user-read-currently-playing"`.
- **Disk space**: Plugin installation triggers uv dependency resolution which needs disk space. If `hermes plugins enable` fails with "No space left on device", clean caches first (`rm -rf ~/.hermes/cache/uv`), then manually edit config.yaml if the command still fails.
- **Tool availability**: After enabling the plugin and toolset, the Spotify tools are NOT available in the current session. A gateway restart or new session is required.
- **Token refresh**: Tokens are refreshed automatically. If auth fails with 401 after retry, run `hermes spotify login` again (client_id is saved in .env, so it skips that step).
- **Free vs Premium**: Search, playlists, albums, library, queue reads, device lists, and playback state work on Free. Playback control (play, pause, skip, seek, volume, shuffle/repeat, queue add, transfer) needs Premium and an active Spotify Connect device.

## Environment Variables
- `HERMES_SPOTIFY_CLIENT_ID`: Spotify app Client ID (set by login wizard)
- `HERMES_SPOTIFY_REDIRECT_URI`: Override redirect URI (default: http://127.0.0.1:43827/spotify/callback)
