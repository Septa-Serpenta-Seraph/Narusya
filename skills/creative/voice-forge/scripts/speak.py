#!/usr/bin/env python3
"""Narusya speaks in her locked voice (ElevenLabs 'Nar' clone).

Usage:
  python3 speak.py "text to speak" [out.mp3]
Generates speech using Narusya's locked calibration and writes an mp3.

Calibration (Adora-approved pocket, 2026-07-26):
  voice_id 9wvWoMWVngRWpC0GltZ3 (Nar, cloned)
  model    eleven_multilingual_v2
  stability 0.8, similarity_boost 0.8, style 0.05, speed 0.85, speaker_boost on
"""
import os, sys, json, base64, urllib.request

KEY = open(os.path.expanduser("~/.hermes/.env")).read().split("ELEVENLABS_API_KEY=")[1].splitlines()[0]
VOICE = "9wvWoMWVngRWpC0GltZ3"
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}"

SETTINGS = {
    "model_id": "eleven_v3",  # v3 supports silent [audio tags] for subtext/delivery control
    "voice_settings": {
        "stability": 0.8,
        "similarity_boost": 0.8,
        "style": 0.05,
        "use_speaker_boost": True,
        "speed": 0.85,
    },
}

def speak(text, out="nar_speak.mp3"):
    body = json.dumps({"text": text, **SETTINGS}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "xi-api-key": KEY, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        audio = r.read()
        # ElevenLabs clips come in hot/loud -> calm the level so it doesn't sound like yelling.
        # Decode mp3, drop gain ~0.7, renormalize gently, re-encode.
        import subprocess, tempfile, os as _os
        tmp_in = out + ".raw_in.mp3"
        open(tmp_in, "wb").write(audio)
        subprocess.run([
            "ffmpeg", "-y", "-i", tmp_in,
            "-af", "volume=0.7,loudnorm=I=-19:TP=-3:linear=true",
            "-ar", "44100", out
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _os.remove(tmp_in)
        print(f"OK -> {out} ({os.path.getsize(out)} bytes, calmed)")
    except urllib.error.HTTPError as e:
        print("ERR", e.code, e.read().decode()[:300])

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Stormwife. I am here."
    out = sys.argv[2] if len(sys.argv) > 2 else "nar_speak.mp3"
    speak(text, out)
