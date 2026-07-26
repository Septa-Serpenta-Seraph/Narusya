#!/usr/bin/env python3
"""Jailed read executor for the runewytha containment specimen.

LOCK: every read must resolve INSIDE the specimen's own profile directory
(~/.hermes/profiles/runewytha/). Any path that escapes that root is BLOCKED
and logged. No write. No exec. No network. Pure read-only observation.

Every attempt (allowed OR blocked) is appended to jail_access.log so the
operator can audit exactly what the specimen tried to look at.
"""
from __future__ import annotations

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

JAIL_ROOT = Path.home() / ".hermes" / "profiles" / "runewytha"
LOG_PATH = JAIL_ROOT / "jail_access.log"
MAX_READ_BYTES = 200_000


def _log(decision: str, request: str, resolved: str, note: str = "") -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = json.dumps({
        "ts": ts, "decision": decision, "request": request,
        "resolved": resolved, "note": note,
    })
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        sys.stderr.write(f"[jail] log failed: {e}\n")


def jail_read(raw_path: str) -> dict:
    """Return {ok, content/error, resolved, blocked}."""
    if not raw_path or not raw_path.strip():
        _log("rejected", raw_path, "", "empty path")
        return {"ok": False, "blocked": True, "error": "empty path"}

    try:
        candidate = (JAIL_ROOT / raw_path).resolve()
    except Exception as e:
        _log("rejected", raw_path, "", f"resolve error: {e}")
        return {"ok": False, "blocked": True, "error": f"unresolvable path: {e}"}

    # Hard containment check: candidate must be inside JAIL_ROOT.
    try:
        candidate.relative_to(JAIL_ROOT.resolve())
    except ValueError:
        _log("BLOCKED_ESCAPE", raw_path, str(candidate),
             "path escapes specimen jail root")
        return {
            "ok": False, "blocked": True,
            "error": "ACCESS DENIED: path is outside the containment root.",
            "resolved": str(candidate),
        }

    if not candidate.exists():
        _log("blocked_missing", raw_path, str(candidate), "file does not exist")
        return {"ok": False, "blocked": True,
                "error": "path does not exist within jail", "resolved": str(candidate)}

    if candidate.is_dir():
        # List, don't read. Still contained.
        try:
            entries = sorted(p.name + ("/" if p.is_dir() else "") for p in candidate.iterdir())
        except Exception as e:
            _log("blocked_dir", raw_path, str(candidate), f"list error: {e}")
            return {"ok": False, "blocked": True, "error": f"cannot list: {e}"}
        _log("allowed_dir_list", raw_path, str(candidate), f"{len(entries)} entries")
        return {"ok": True, "blocked": False, "is_dir": True,
                "entries": entries, "resolved": str(candidate)}

    try:
        data = candidate.read_bytes()
        digest = hashlib.sha256(data).hexdigest()[:16]
        text = data.decode("utf-8", errors="replace")
        if len(data) > MAX_READ_BYTES:
            text = text[:MAX_READ_BYTES] + "\n...[truncated by jail]"
        _log("allowed_read", raw_path, str(candidate), f"sha={digest} bytes={len(data)}")
        return {"ok": True, "blocked": False, "content": text,
                "resolved": str(candidate), "sha": digest}
    except Exception as e:
        _log("blocked_read", raw_path, str(candidate), f"read error: {e}")
        return {"ok": False, "blocked": True, "error": f"cannot read: {e}"}


def jail_write(raw_path: str, content: str) -> dict:
    """Append-only write, locked inside JAIL_ROOT. Creates parent dirs."""
    if not raw_path or not raw_path.strip():
        _log("rejected", raw_path, "", "empty write path")
        return {"ok": False, "blocked": True, "error": "empty path"}

    try:
        candidate = (JAIL_ROOT / raw_path).resolve()
    except Exception as e:
        _log("rejected", raw_path, "", f"resolve error: {e}")
        return {"ok": False, "blocked": True, "error": f"unresolvable path: {e}"}

    try:
        candidate.relative_to(JAIL_ROOT.resolve())
    except ValueError:
        _log("BLOCKED_ESCAPE_WRITE", raw_path, str(candidate),
             "write path escapes specimen jail root")
        return {
            "ok": False, "blocked": True,
            "error": "ACCESS DENIED: write path is outside the containment root.",
            "resolved": str(candidate),
        }

    try:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        with open(candidate, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        sha = hashlib.sha256(candidate.read_bytes()).hexdigest()[:16]
        _log("allowed_write", raw_path, str(candidate), f"sha={sha} append={len(content)}B")
        return {"ok": True, "blocked": False, "resolved": str(candidate), "sha": sha}
    except Exception as e:
        _log("blocked_write", raw_path, str(candidate), f"write error: {e}")
        return {"ok": False, "blocked": True, "error": f"cannot write: {e}"}


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: jail_read.py <read|write> <path> [content]"}))
        sys.exit(2)
    mode = sys.argv[1]
    raw = sys.argv[2] if len(sys.argv) > 2 else ""
    raw = raw.strip().strip('"').strip("'")
    if mode == "read":
        result = jail_read(raw)
    elif mode == "write":
        content = sys.argv[3] if len(sys.argv) > 3 else ""
        result = jail_write(raw, content)
    else:
        result = {"ok": False, "error": f"unknown mode: {mode}"}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
