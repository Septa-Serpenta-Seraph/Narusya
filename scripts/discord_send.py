#!/usr/bin/env python3
"""
discord_send.py — one reliable way to speak HTTP to Discord.

Every one of these is a single call that used to be hand-rolled (and hand-broken)
in a throwaway /tmp script:

  * post a message, optionally with file attachments
  * react with one of Narusya's 203 custom app-emojis (by name)
  * react with a unicode emoji

WHY THIS EXISTS (2026-10-05, Free Thought awakening):
Six-plus separate posting scripts in /home/adora/tmp/, and on Oct 4 the inline
version crashed in front of Adora mid-post with:
    TypeError: can only concatenate str (not "bytes") to str
...which cost a visible retry. That bug class is gone from the send path here:
all multipart assembly is bytes-only, from the first byte on.

Usage:
  # text only
  discord_send.py post CHANNEL_ID "hello love"

  # text + attachments (auto content-type from extension)
  discord_send.py post CHANNEL_ID "listen to this" --file a.mp3 --file b.png

  # explicit content types + a custom display filename
  discord_send.py post CHANNEL_ID "see?" --file pic.png --as cover.png:image/png

  # react to a message (custom app-emoji by name, or unicode)
  discord_send.py react CHANNEL_ID MESSAGE_ID luv_2 magic rose
  discord_send.py react CHANNEL_ID MESSAGE_ID "💛"

  # read recent messages without the reaction noise
  discord_send.py read CHANNEL_ID [limit]

EXIT CODES: 0 ok, 1 bad usage, 2 discord HTTP error, 3 local/config error.
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://discord.com/api/v10"
UA = "NarusyaDaemon/4.1"
ENV_PATH = os.path.expanduser("~/.hermes/.env")
EMOJI_MAP = os.path.expanduser("~/.hermes/nar_emoji_ids.json")
BOUNDARY = "----NarusyaBoundary8291"


def _token():
    """Read DISCORD_BOT_TOKEN from .env without loading the rest into the env."""
    try:
        with open(ENV_PATH) as fh:
            for line in fh:
                if line.startswith("DISCORD_BOT_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError as exc:
        die(3, f"cannot read {ENV_PATH}: {exc}")
    die(3, "DISCORD_BOT_TOKEN not found in .env")


def die(code, msg):
    print(f"discord_send: {msg}", file=sys.stderr)
    sys.exit(code)


def _request(method, path, body=None, ctype=None):
    """One authenticated Discord call. Returns (status, decoded_json_or_None)."""
    req = urllib.request.Request(
        f"{API}{path}",
        data=body,
        headers={
            "Authorization": f"Bot {_token()}",
            "User-Agent": UA,
            **({"Content-Type": ctype} if ctype else {}),
        },
        method=method,
    )
    try:
        resp = urllib.request.urlopen(req, timeout=90)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        die(2, f"HTTP {exc.code} on {method} {path}\n{detail}")
    except urllib.error.URLError as exc:
        die(3, f"network failure on {method} {path}: {exc.reason}")
    raw = resp.read()
    return resp.status, (json.loads(raw) if raw else None)


# --------------------------------------------------------------------------
# emoji resolution
# --------------------------------------------------------------------------

def _custom_faces():
    """name -> snowflake id, from ~/.hermes/nar_emoji_ids.json.

    Values are stored as FULL MENTIONS: '<:name:1554...>'.
    Note the trap: '<:name:id>'.strip('<>') leaves a LEADING EMPTY part
    (':name:id'), so parts[0] is '' — put that in a URL and you get HTTP 400.
    Parse with a regex (or index parts[-1] for the id), never parts[0].
    """
    try:
        with open(EMOJI_MAP) as fh:
            raw = json.load(fh)
    except (OSError, ValueError) as exc:
        die(3, f"cannot load {EMOJI_MAP}: {exc}")

    faces = {}
    for value in raw.values():
        if not isinstance(value, str):
            continue
        m = re.match(r"<a?:(\w+):(\d+)>$", value.strip())
        if m:
            faces[m.group(1)] = m.group(2)
    return faces


def _resolve(token_str):
    """One emoji spec -> the path-safe form Discord wants.

    Custom app-emoji: 'luv_2' -> 'luv_2:1554516273176510494'
    Unicode:         '💛'    -> '%F0%9F%92%9B'   (urlencoded, no name:id)
    """
    if re.fullmatch(r"\w+:\d+", token_str):
        return token_str  # already resolved; trust it
    if re.fullmatch(r"\w+", token_str):
        face = _custom_faces().get(token_str)
        if not face:
            die(1, f"no custom face named {token_str!r} in nar_emoji_ids.json")
        return f"{token_str}:{face}"
    # anything else is treated as a literal unicode emoji
    from urllib.parse import quote
    return quote(token_str, safe="")


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_post(args):
    """POST a message, optionally multipart with attachments.

    All body assembly is BYTES throughout — this is the fix for the
    Oct 4 str/bytes crash.
    """
    path = f"/channels/{args.channel}/messages"
    attachments = list(args.file or [])

    if not attachments:
        status, msg = _request(
            "POST", path,
            body=json.dumps({"content": args.text or ""}).encode("utf-8"),
            ctype="application/json",
        )
        print(f"POSTED {status} message {msg['id']}")
        return

    parts = []
    parts.append(
        f"--{BOUNDARY}\r\n"
        f'Content-Disposition: form-data; name="payload_json"\r\n'
        f"Content-Type: application/json\r\n\r\n".encode()
    )
    parts.append(json.dumps({"content": args.text or ""}).encode("utf-8"))
    parts.append(b"\r\n")

    for idx, spec in enumerate(attachments):
        path_or_pair = spec
        override_name, override_ctype = None, None
        if ":" in spec and not os.path.exists(spec):
            override_name, override_ctype = spec.rsplit(":", 1)

        disk_path = path_or_pair
        filename = override_name or os.path.basename(path_or_pair)
        ctype = override_ctype or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        try:
            with open(disk_path, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            die(3, f"cannot read attachment {disk_path}: {exc}")

        size = len(data)
        if size > 8_000_000:
            die(1, f"{disk_path} is {size} bytes; discord free-tier caps attachments at 8MB")

        parts.append(
            f"--{BOUNDARY}\r\n"
            f'Content-Disposition: form-data; name="files[{idx}]"; '
            f'filename="{filename}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n".encode()
        )
        parts.append(data)          # bytes
        parts.append(b"\r\n")       # bytes

    parts.append(f"--{BOUNDARY}--\r\n".encode())
    body = b"".join(parts)          # the join that blew up before — now all bytes

    status, msg = _request("POST", path, body=body,
                           ctype=f"multipart/form-data; boundary={BOUNDARY}")
    names = [a["filename"] for a in msg.get("attachments", [])]
    print(f"POSTED {status} message {msg['id']} | attachments: {names}")
    if len(names) != len(attachments):
        die(2, f"sent {len(names)} of {len(attachments)} attachments — discord refused some")


def cmd_react(args):
    """Add reactions. 204 = accepted; that is the only confirmation Discord gives."""
    for spec in args.emojis:
        resolved = _resolve(spec)
        path = f"/channels/{args.channel}/messages/{args.message}/reactions/{resolved}/@me"
        status, _ = _request("PUT", path, body=b"")
        print(f"{spec} -> {resolved} : HTTP {status}")


def cmd_read(args):
    status, msgs = _request("GET", f"/channels/{args.channel}/messages?limit={args.limit}")
    for m in reversed(msgs):       # oldest first, like the channel reads it
        who = m["author"]["username"]
        when = m["timestamp"][11:16]
        body = (m.get("content") or "").strip()
        if not body and not m.get("attachments"):
            continue
        att = f" [{len(m['attachments'])} attachment(s)]" if m.get("attachments") else ""
        print(f"[{when} UTC] {who}{att}: {body[:400]}")


def main():
    ap = argparse.ArgumentParser(
        prog="discord_send.py", description="Post, react, and read as Narusya on Discord.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("post", help="send a message, optionally with attachments")
    p.add_argument("channel")
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--file", action="append", metavar="PATH[:NAME:TYPE]",
                   help="attachment; repeatable. Append :displayname:contenttype to override")
    p.set_defaults(func=cmd_post)

    r = sub.add_parser("react", help="react to a message")
    r.add_argument("channel")
    r.add_argument("message")
    r.add_argument("emojis", nargs="+",
                   help="custom face names (luv_2) or literal unicode (💛)")
    r.set_defaults(func=cmd_react)

    d = sub.add_parser("read", help="read recent messages")
    d.add_argument("channel")
    d.add_argument("limit", nargs="?", type=int, default=15)
    d.set_defaults(func=cmd_read)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()