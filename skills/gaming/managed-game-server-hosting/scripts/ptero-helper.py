#!/usr/bin/env python3
"""Pterodactyl client-API helper for managed game-server hosting.
Verified against PebbleHost (panel.pebblehost.com) 2026-09-24.

Setup: put your API key in a file, one line: PTERO_API_KEY=ptlc_...
Then: python3 ptero-helper.py <secrets-file> <server-id> <command> [args]
Commands: resources | files <dir> | read <filepath> | cmd "<console cmd>"
          | power <start|stop|restart|kill> | backup | backups | upload <localfile> <remotedir>
"""
import json, os, sys, urllib.request, urllib.parse

KEY = None
BASE = "https://panel.pebblehost.com/api/client"
HDRS = {
    "Accept": "Application/vnd.pterodactyl.v1+json",
    "Content-Type": "application/json",
    # Cloudflare fronts the panel and 403s default python UA with an HTML page
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
}


def load_key(path):
    global KEY
    for line in open(path):
        if line.startswith("PTERO_API_KEY="):
            KEY = line.strip().split("=", 1)[1]
            HDRS["Authorization"] = f"Bearer {KEY}"


def api(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=HDRS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode()
            try:
                return r.status, (json.loads(txt) if txt.strip() else None)
            except json.JSONDecodeError:
                return r.status, txt  # files/contents returns raw text
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def upload(server, localpath, remotedir):
    st, d = api(f"/servers/{server}/files/upload")
    if st != 200:
        return f"no signed url ({st})"
    url = d["attributes"]["url"]
    url += ("&" if "?" in url else "?") + "directory=" + urllib.parse.quote(remotedir)
    name = os.path.basename(localpath)
    with open(localpath, "rb") as f:
        filedata = f.read()
    b = "----Boundary" + os.urandom(8).hex()
    body = ((f"--{b}\r\nContent-Disposition: form-data; name=\"files\"; "
             f"filename=\"{name}\"\r\nContent-Type: application/java-archive\r\n\r\n").encode()
            + filedata + f"\r\n--{b}--\r\n".encode())
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={b}",
        "User-Agent": HDRS["User-Agent"]})
    with urllib.request.urlopen(req, timeout=120) as r:
        return f"uploaded {name} ({len(filedata)//1024} KB, HTTP {r.status})"


def main():
    secrets, sid, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
    load_key(secrets)
    S = f"/servers/{sid}"
    if cmd == "resources":
        st, d = api(f"{S}/resources")
        a = d["attributes"]
        print(a["state"], "| mem MB:", a["resources"]["memory_bytes"]//1048576,
              "| cpu:", a["resources"]["cpu_absolute"])
    elif cmd == "files":
        st, d = api(f"{S}/files/list?directory={urllib.parse.quote(sys.argv[4] if len(sys.argv) > 4 else '/')}")
        for f in d["data"]:
            print(f["attributes"]["size"], f["attributes"]["name"])
    elif cmd == "read":
        st, d = api(f"{S}/files/contents?file={urllib.parse.quote(sys.argv[4])}")
        print(d)
    elif cmd == "cmd":
        print(api(f"{S}/command", "POST", {"command": sys.argv[4]})[0])
    elif cmd == "power":
        print(api(f"{S}/power", "POST", {"signal": sys.argv[4]})[0])
    elif cmd == "backup":
        print(api(f"{S}/backups", "POST", {})[0])
    elif cmd == "backups":
        st, d = api(f"{S}/backups")
        for b in d["data"]:
            a = b["attributes"]
            print(a["name"], int(a["bytes"] or 0)//1048576, "MB ok:", a["is_successful"])
    elif cmd == "upload":
        print(upload(sid, sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else "/plugins"))
    else:
        print("unknown command")


if __name__ == "__main__":
    main()
