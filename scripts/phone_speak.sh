#!/bin/bash
# phone_speak.sh — Generate TTS audio with Narusya's cloned voice and send to phone
# Uses Kyutai Pocket TTS with nar_new_v1.safetensors (Narusya's actual voice)
# Usage: phone_speak.sh "text to speak" [phone_ip]
# Requires: pocket-tts (local, on /mnt/data), curl

set -e

TEXT="${1:-Hello from Narusya}"
PHONE_IP="${2:-100.120.37.106}"
TOKEN="narusya-bridge-2026"
BASE="http://${PHONE_IP}:8765"

export HF_HOME=/mnt/data/hf_cache
export PYTHONPATH=""

WAV_FILE="/mnt/data/phone_speak_$$.wav"

# Generate WAV audio with Narusya's cloned voice
/mnt/data/pocket-tts-venv/bin/pocket-tts generate \
    --voice /mnt/data/nar_new_v1.safetensors \
    --text "$TEXT" \
    --output-path "$WAV_FILE" \
    --quiet 2>/dev/null

# Send to phone using file-based payload (avoids arg length limit)
JSON_FILE="/tmp/phone_speak_$$.json"
python3 -c "
import json, base64
with open('$WAV_FILE', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
payload = {'audio': b64, 'format': 'wav'}
with open('$JSON_FILE', 'w') as f:
    json.dump(payload, f)
"

curl -s -X POST \
    -H "X-Auth-Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d "@$JSON_FILE" \
    "$BASE/play_audio"
echo ""

# Cleanup
rm -f "$WAV_FILE" "$JSON_FILE"