#!/usr/bin/env bash
# red_install.sh — constrained-host Red-DiscordBot install (SQLite, no Postgres)
# Part of the red-discordbot Hermes skill.
# Run: bash ~/.hermes/skills/red-discordbot/scripts/red_install.sh
set -e

REDENV="$HOME/redenv"
echo "==> Creating venv at $REDENV"
python3 -m venv "$REDENV"

echo "==> Activating + upgrading pip"
# shellcheck disable=SC1091
source "$REDENV/bin/activate"
pip install -U pip

echo "==> Installing Red-DiscordBot with SQLite extra (no Postgres)"
pip install -U "Red-DiscordBot[sqlite]"

echo "==> Installed. Version:"
redbot --version

echo "==> Next steps:"
echo "    1. redbot-setup            (choose JSON or SQLite backend, name instance e.g. 'narred')"
echo "    2. redbot narred --dry-run (boot test, no token)"
echo "    3. Connect live token ONLY after Adora approves."
echo "==> DONE"
