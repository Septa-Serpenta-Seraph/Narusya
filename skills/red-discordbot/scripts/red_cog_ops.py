#!/usr/bin/env python3
"""red_cog_ops.py — Red cog inspection + command helper for Narusya.

IMPORTANT: Red has NO non-interactive CLI for `cog load/unload/reload`.
Those are issued as in-guild Discord commands while the bot runs with a token:
    [p]load <cog>   [p]reload <cog>   [p]unload <cog>   [p]cog list
(Or via the bot REPL.) This script therefore:
  - list:           scans instance data dir + venv for installed cog packages
  - load/unload/reload: prints the exact [p] command to run in Discord

Usage:
    python3 red_cog_ops.py <instance> <list|load|unload|reload> [cog]
"""
import os
import sys
import glob

DATA_DEFAULT = "/home/adora/reddata"


def find_cogs():
    found = []
    # User-installed cogs live under <data>/cogs/<name>/__init__.py
    data_cogs = os.path.join(DATA_DEFAULT, "cogs")
    if os.path.isdir(data_cogs):
        for d in sorted(os.listdir(data_cogs)):
            p = os.path.join(data_cogs, d)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "__init__.py")):
                found.append(("user", d))
    # Bundled cogs ship inside the venv redbot/cogs
    venv_cogs = os.path.join(os.path.expanduser("~/redenv"), "lib", "*", "redbot", "cogs")
    for path in glob.glob(venv_cogs):
        if os.path.isdir(path):
            for d in sorted(os.listdir(path)):
                if os.path.isdir(os.path.join(path, d)):
                    found.append(("bundled", d))
    return found


def main():
    if len(sys.argv) < 3:
        print("usage: red_cog_ops.py <instance> <list|load|unload|reload> [cog]")
        sys.exit(1)
    instance = sys.argv[1]
    op = sys.argv[2]
    cog = sys.argv[3] if len(sys.argv) > 3 else None

    if op == "list":
        cogs = find_cogs()
        print(f"Installed cogs (instance '{instance}'):")
        if not cogs:
            print("  (none found under", DATA_DEFAULT, "or venv)")
        for kind, name in cogs:
            print(f"  [{kind}] {name}")
    elif op in ("load", "unload", "reload"):
        if not cog:
            print(f"op '{op}' requires a cog name")
            sys.exit(1)
        print("Red has no CLI for cog ops. Run this in a Discord channel the bot can see:")
        print(f"  [p]{op} {cog}")
        print("  (default prefix is [p]; change via [p]prefix if needed)")
    else:
        print(f"unknown op: {op}")
        sys.exit(1)


if __name__ == "__main__":
    main()
