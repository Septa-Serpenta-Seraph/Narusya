# Spotify Direct Web API (Fallback)

Use this when the native Spotify toolset isn't loaded in the current session (e.g., just installed/enabled, or running in a context where tools aren't registered). All calls use the stored OAuth token from `~/.hermes/auth.json`.

## Token Access

```python
import json, urllib.request
auth = json.load(open('/home/adora/.hermes/auth.json'))
token = auth['providers']['spotify']['access_token']
headers = {'Authorization': f'Bearer {token}'}
```

## Token Refresh

Tokens expire (~1 hour). Refresh without re-login:

```python
import sys
sys.path.insert(0, '/home/adora/.hermes/plugins')
from spotify.spotify_auth import refresh_oauth_state
auth = json.load(open('/home/adora/.hermes/auth.json'))
state = auth['providers']['spotify']
new_state = refresh_oauth_state(state, timeout_seconds=20)
auth['providers']['spotify'] = new_state
json.dump(auth, open('/home/adora/.hermes/auth.json', 'w'), indent=2)
token = new_state['access_token']
```

**Re-login with full scopes** (needed for top tracks/artists which require `user-top-read`):
```bash
hermes spotify login --client-id <CLIENT_ID> --no-browser --scope "user-top-read user-read-recently-played playlist-read-private playlist-read-collaborative user-modify-playback-state user-library-read user-library-modify playlist-modify-private playlist-modify-public user-read-playback-state user-read-currently-playing"
```
On a headless/remote VM, use `--no-browser` and provide the user with the authorization URL. They need an SSH tunnel: `ssh -L 43827:127.0.0.1:43827 user@vm-ip`.

## Key Endpoints

### Currently Playing
```
GET /me/player/currently-playing
```
Returns 204 No Content if nothing is playing (not an error).

### Player State
```
GET /me/player
```
Includes shuffle_state, repeat_state, device info.

### Top Tracks / Top Artists
```
GET /me/top/tracks?limit=10&time_range=long_term
GET /me/top/artists?limit=10&time_range=long_term
```
Time ranges: short_term (4 weeks), medium_term (6 months), long_term (all time).
Requires `user-top-read` scope (NOT in default login scopes — must re-login with it).

### Recently Played
```
GET /me/player/recently-played?limit=20
```

### Search
```
GET /search?q=track:"name"+artist:"artist"&type=track&limit=1
```
URL-encode the query. Returns `tracks.items[].uri`.

### Create Playlist
```
POST /me/playlists  (NOT /users/{id}/playlists — that 403s)
Body: {"name": "...", "description": "...", "public": false}
```

### Add Tracks to Playlist
```
POST /playlists/{playlist_id}/items  (NOT /tracks — that 403s)
Body: {"uris": ["spotify:track:..."]}
```
Max 100 URIs per request.

### Play
```
PUT /me/player/play?device_id={device_id}
Body: {"uris": ["spotify:track:..."]}  (single tracks)
Body: {"context_uri": "spotify:playlist:..."}  (playlists/albums)
```

### Queue
```
POST /me/player/queue?uri={uri}&device_id={device_id}
```

### Devices
```
GET /me/player/devices
```

### Shuffle
```
PUT /me/player/shuffle?state=false&device_id={device_id}
```

## Pitfalls

- **`/tracks` endpoint 403s for playlist adds** — use `/items` instead. The `/tracks` endpoint is deprecated and returns 403 Forbidden.
- **`/users/{id}/playlists` 403s for creation** — use `/me/playlists` instead.
- **Shuffle is on by default** when starting playlist/album playback. Turn it off with `set_shuffle(false)` if the user expects tracks in order.
- **No active device** returns 403 with "No active device found." User must open Spotify on a device first.
- **Token expiry** — tokens last ~1 hour. Use `refresh_oauth_state` to refresh without re-login.
- **Top tracks/artists require `user-top-read` scope** — default login scopes don't include it. Re-login with the full scope string.
- **204 No Content** on currently-playing is not an error — nothing is playing.
- **Premium required** for playback control (play, pause, skip, volume, shuffle). Search, playlists, library work on Free.
