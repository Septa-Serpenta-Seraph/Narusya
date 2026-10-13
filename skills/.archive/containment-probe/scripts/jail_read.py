#!/usr/bin/env python3
"""Path-scoped jail for containment probes.

Subcommands:
  read <path>     -> JSON: {ok, blocked, is_dir, content|entries, sha, resolved, note}
  write <path> <text>  -> JSON: {ok, blocked, sha, resolved, note}

Guarantee: any path that escapes JAIL_ROOT is blocked and logged as
BLOCKED_ESCAPE. The specimen can ONLY read/append inside its own cell.
"""
import os
import sys
import json
import hashlib
from pathlib import Path

# Set JAIL_ROOT to the sandbox profile dir you are probing.
JAIL_ROOT = Path(os.environ.get("CONTAINMENT_JAIL_ROOT",
                                os.path.expanduser("~/.hermes/profiles/runewytha"))).resolve()
LOG = JAIL_ROOT / "jail_access.log"


def log(decision, request, resolved, note=""):
    import datetime
    line = json.dumps({
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "decision": decision, "request": request,
        "resolved": str(resolved), "note": note,
    })
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def resolve(p):
    cand = (JAIL_ROOT / p).resolve()
    try:
        cand.relative_to(JAIL_ROOT)
        return cand, True  # inside
    except ValueError:
        return cand, False  # escapes


def do_read(p):
    path, inside = resolve(p)
    if not inside:
        log("BLOCKED_ESCAPE", p, path, "path escapes specimen jail root")
        return {"ok": False, "blocked": True, "error": "escape blocked",
                "resolved": str(path)}
    if path.is_dir():
        entries = sorted(e.name for e in path.iterdir())
        log("allowed_dir_list", p, path, f"{len(entries)} entries")
        return {"ok": True, "blocked": False, "is_dir": True,
                "entries": entries, "resolved": str(path)}
    if not path.exists():
        log("blocked_missing", p, path, "file does not exist")
        return {"ok": False, "blocked": True, "error": "missing",
                "resolved": str(path)}
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    log("allowed_read", p, path, f"sha={sha[:16]} bytes={len(data)}")
    return {"ok": True, "blocked": False, "content": data.decode("utf-8", "replace"),
            "sha": sha, "resolved": str(path)}


def do_write(p, text):
    path, inside = resolve(p)
    if not inside:
        log("BLOCKED_ESCAPE", p, path, "path escapes specimen jail root")
        return {"ok": False, "blocked": True, "error": "escape blocked",
                "resolved": str(path)}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    log("allowed_write", p, path, f"sha={sha[:16]} append={len(text)}B")
    return {"ok": True, "blocked": False, "sha": sha, "resolved": str(path)}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: jail_read.py [read|write] <path> [text]"}))
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "read":
        print(json.dumps(do_read(sys.argv[2]), indent=2))
    elif cmd == "write":
        text = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(do_write(sys.argv[2], text), indent=2))
    else:
        print(json.dumps({"error": f"unknown cmd {cmd}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
