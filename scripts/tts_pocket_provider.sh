#!/bin/bash
# Kyutai Pocket TTS provider wrapper for Hermes command-type TTS.
# Usage: tts_pocket_provider.sh <text_file> <output_mp3>
# Reads the text from <text_file>, speaks it with Narusya's cloned Nar voice
# (offline Kyutai Pocket TTS), and writes an MP3 to <output_mp3>.
set -euo pipefail
export PYTHONPATH=""
export HF_HOME=/mnt/data/hf_cache
TEXT="$(cat "$1")"
exec python3 /home/adora/narusya_voice/speak_pocket.py "$TEXT" "$2"
