# Plugin Install Recipe: Modrinth → Pterodactyl Panel (PebbleHost-proven)

End-to-end flow for adding a Bukkit/Paper plugin to a panel-hosted server. Worked example from 2026-09-25: user group wanted 'torches light without being placed' (held-torch dynamic light).

## 1. Find the plugin on Modrinth API

Search with facets as array-of-arrays (bare bracket strings → HTTP 400):
```python
facets = json.dumps([["categories:bukkit"], ["project_type:plugin"]])
url = ("https://api.modrinth.com/v2/search?" +
       urllib.parse.urlencode({"query": "torch light", "facets": facets, "limit": 20}))
```
Judge candidates by downloads + recency + description fit, then load `/v2/project/{slug}/version` for files.

Pick the newest version whose `game_versions` is closest to the server's MC version. Server version comes from the panel `JARFILE` startup variable (e.g. `paper-26.2-129.jar` → Paper 26.2, build 129).

## 2. Version-gap rule
A plugin listing e.g. 26.1.x but not 26.2 is usually still fine — point releases rarely break plugin APIs. Install, then judge from the boot log, not the version list.

## 3. Download locally, then upload via panel

```python
urllib.request.urlretrieve(JAR_URL, "/tmp/Plugin-1.1.0.jar")

# 3a. get signed upload URL
st, data = api(f"/servers/{SID}/files/upload")
upload_url = data["attributes"]["url"] + "&directory=%2Fplugins"

# 3b. multipart POST, field name MUST be 'files'
boundary = "----naru-boundary"
body = (f'--{boundary}\r\nContent-Disposition: form-data; name="files"; '
        f'filename="Plugin-1.1.0.jar"\r\nContent-Type: application/java-archive\r\n\r\n'
        ).encode() + jar_bytes + f'\r\n--{boundary}--\r\n'.encode()
```
Verify the jar landed: re-list `/plugins` before restarting.

## 4. Restart and verify

`POST /power {"signal": "restart"}` → wait ~30-60s → read `/logs/latest.log` and confirm the plugin's enable line (e.g. `[TorchHeadLight] Enabling`), no stack trace. Warn players about the restart blip first if anyone is online.

## 5. Foreground-session approval caveat
The full install+restart script can sit pending user approval and time out as 'BLOCKED'. Do not retry or rephrase the same command. Instead: stage the jar URL and plan, present the user a short plan (plugin, version, version-gap caveat, restart warning), and wait for explicit go. On go, re-run in one batch.

## Candidate pool (torch-light family, checked 2026-09-25)
- **TorchHeadLight** (`torchheadlight`) — dynamic held-light, Paper/bukkit/purpur, v1.1.0 supports 1.21.8–26.1.2, 13KB. Selected.
- **NM Auto Torch** (`nm-auto-torch`) — auto-places torches while exploring caves; different mechanic (places real torches), not dynamic light.
