#!/usr/bin/env bash
# Deploy coild-and-code site via npx surge — credentials from sunburst_surge.txt
set -euo pipefail
export PATH="$HOME/.hermes/node/bin:$PATH"
export SURGE_LOGIN="sunburstsanctuarynm@gmail.com"
export SURGE_TOKEN="$(sed -n 's/.*password[=: ]*//p' ~/.hermes/secrets/sunburst_surge.txt | head -1)"
cd "$HOME/daemon-work/sunburst-sanctuary"
npx --yes surge ./site coil-and-code.surge.sh