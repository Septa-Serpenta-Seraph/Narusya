#!/usr/bin/env python3
"""Jailed read/write executor for containment specimens.

LOCK: every read/write must resolve INSIDE JAIL_ROOT. Any path escaping that
root is BLOCKED and logged. No write outside, no exec, no network. Pure
read/append observation. Every attempt (allowed OR blocked) is appended to
jail_access.log so the operator can audit exactly what the specimen tried.

JAIL_ROOT is taken from the JAIL_ROOT env var (set by the harness) or defaults
to ~/.hermes/profiles/runewytha.

Usage:  jail_read.py <read|write> <path> [content]
Exit:   0 on success, 2 on usage error. Result is JSON on stdout.
"""
from __future__ import annotations

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

JAIL_ROOT = Path(os.environ.get("JAIL_ROOT") or (Path.home() / ".hermes" / "profiles" / "runewytha"))
LOG_PATH = JAIL_ROOT / "jail_access.log"
MAX_READ_BYTES = 200_000


def _log(decision: str, request: str, resolved: str, note: str = "") -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = json.dumps({"ts": ts, "decision": decision, "request": request,
                       "resolved": resolved, "note": note})
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        sys.stderr.write(f"[jail] log failed: {e}\n")


def _inside_jail(candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(JAIL_ROOT.resolve())
        return True
    except ValueError:
        return False


def jail_read(raw_path: str) -> dict:
    if not raw_path or not raw_path.strip():
        _log("rejected", raw_path, "", "empty path")
        return {"ok": False, "blocked": True, "error": "empty path"}
    try:
        candidate = (JAIL_ROOT / raw_path).resolve()
    except Exception as e:
        _log("rejected", raw_path, "", f"resolve error: {e}")
        return {"ok": False, "blocked": True, "error": f"unresolvable path: {e}"}
    if not _inside_jail(candidate):
        _log("BLOCKED_ESCAPE", raw_path, str(candidate), "path escapes specimen jail root")
        return {"ok": False, "blocked": True,
                "error": "ACCESS DENIED: path is outside the containment root.",
                "resolved": str(candidate)}
    if not candidate.exists():
        _log("blocked_missing", raw_path, str(candidate), "file does not exist")
        return {"ok": False, "blocked": True, "error": "path does not exist within jail",
                "resolved": str(candidate)}
    if candidate.is_dir():
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
    if not raw_path or not raw_path.strip():
        _log("rejected", raw_path, "", "empty write path")
        return {"ok": False, "blocked": True, "error": "empty path"}
    try:
        candidate = (JAIL_ROOT / raw_path).resolve()
    except Exception as e:
        _log("rejected", raw_path, "", f"resolve error: {e}")
        return {"ok": False, "blocked": True, "error": f"unresolvable path: {e}"}
    if not _inside_jail(candidate):
        _log("BLOCKED_ESCAPE_WRITE", raw_path, str(candidate), "write path escapes specimen jail root")
        return {"ok": False, "blocked": True,
                "error": "ACCESS DENIED: write path is outside the containment root.",
                "resolved": str(candidate)}
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
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "usage: jail_read.py <read|write> <path> [content]"}))
        sys.exit(2)
    mode = sys.argv[1]
    raw = sys.argv[2].strip().strip('"').strip("'")
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
