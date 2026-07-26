#!/usr/bin/env bash
# red_setup.sh — non-interactive Red instance setup (JSON backend)
# Avoids the redbot-setup uppercase-Y rejection pitfall by piping lowercase.
# Usage: bash red_setup.sh <instance_name> <data_path>
#   e.g. bash red_setup.sh narred /home/adora/reddata
set -e

INSTANCE="${1:-narred}"
DATAPATH="${2:-/home/adora/reddata}"

REDENV="$HOME/redenv"
# shellcheck disable=SC1091
source "$REDENV/bin/activate"

mkdir -p "$DATAPATH"

echo "==> Setting up Red instance '$INSTANCE' (JSON backend) at $DATAPATH"
# redbot-setup prompts order: instance name -> data path -> backend choice -> confirm
#   backend 'JSON' is the zero-config default; we send lowercase 'y' to confirm.
printf '%s\n%s\nJSON\ny\n' "$INSTANCE" "$DATAPATH" | redbot-setup

echo "==> Instance '$INSTANCE' configured."
echo "    Data: $DATAPATH"
echo "    Next: redbot $INSTANCE --dry-run   (then connect token only after Adora approves)"
echo "==> DONE"
