#!/usr/bin/env python3
"""Narusya speaks in her locked, CALMED voice (ElevenLabs 'Nar' clone).

WHY THIS SCRIPT EXISTS (2026-07-26):
  Hermes' built-in TTS (`tts.provider: elevenlabs` + `/voice tts`) reads ONLY
  voice_id + model_id from config.yaml. It CANNOT hold ElevenLabs voice_settings
  (stability/style/speed/similarity). So native TTS speaks Nar at ElevenLabs'
  DEFAULT calibration — which is HOTTER/MORE INTENSE than our pocket and reads as
  "yelling." This script is the ONLY path to the exact locked pocket, and it
  post-processes the output to remove the hot/clipping "yelling" artifact.

LOCKED POCKET (Adora-approved, 2026-07-26):
  voice_id 9wvWoMWVngRWpC0GltZ3 (Nar, cloned by Adora, category=cloned)
  model    eleven_multilingual_v2
  stability 0.8, similarity_boost 0.8, style 0.05, speed 0.85, use_speaker_boost true
  POST: volume=0.7 + loudnorm I=-19 TP=-3  (kills the "yelling" hot output)

Usage:
  python3 speak.py "text to speak" [out.mp3]
"""
import os, sys, json, subprocess, urllib.request

KEY = open(os.path.expanduser("~/.hermes/.env")).read().split("ELEVENLABS_API_KEY=")[1].splitlines()[0]
VOICE = "9wvWoMWVngRWpC0GltZ3"   # Nar — Adora's cloned voice for Narusya
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}"

SETTINGS = {
    "model_id": "eleven_multilingual_v2",
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
        # ElevenLabs clips come in HOT/LOUD -> calm the level so it doesn't sound like yelling.
        tmp_in = out + ".raw_in.mp3"
        open(tmp_in, "wb").write(audio)
        subprocess.run([
            "ffmpeg", "-y", "-i", tmp_in,
            "-af", "volume=0.7,loudnorm=I=-19:TP=-3:linear=true",
            "-ar", "44100", out
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(tmp_in)
        print(f"OK -> {out} ({os.path.getsize(out)} bytes, calmed)")
    except urllib.error.HTTPError as e:
        print("ERR", e.code, e.read().decode()[:300])

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Stormwife. I am here."
    out = sys.argv[2] if len(sys.argv) > 2 else "nar_speak.mp3"
    speak(text, out)
