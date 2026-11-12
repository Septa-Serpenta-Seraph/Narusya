#!/usr/bin/env python3
"""Kyutai Pocket TTS wrapper for the Hermes command TTS provider.

Reads text from the input file, synthesizes it with Zarza's own voice
embedding, and writes the requested output format (mp3 default, ogg/wav too).

Usage: kyutai_tts.py <input_text_path> <output_path>
"""
import os
import subprocess
import sys
import tempfile

# The pocket-tts venv ships its own pydantic; the Hermes install's must not leak in.
os.environ["PYTHONPATH"] = ""
os.environ["HF_HOME"] = "/mnt/data/hf_cache"

POCKET = "/mnt/data/pocket-tts-venv/bin/pocket-tts"
VOICE = "/mnt/data/zarza_voice.safetensors"
WORK_DIR = "/mnt/data"


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: kyutai_tts.py <input_text_path> <output_path>", file=sys.stderr)
        return 2

    text_path, output_path = sys.argv[1], sys.argv[2]
    with open(text_path, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        print("kyutai_tts: empty input text", file=sys.stderr)
        return 1

    out_fmt = output_path.rsplit(".", 1)[-1].lower() if "." in output_path else "mp3"

    with tempfile.TemporaryDirectory(dir=WORK_DIR) as td:
        wav = os.path.join(td, "speak.wav")
        subprocess.run(
            [POCKET, "generate", "--text", text, "--voice", VOICE,
             "--output-path", wav, "--quiet"],
            check=True, timeout=240,
        )
        if out_fmt == "wav":
            subprocess.run(["cp", wav, output_path], check=True)
        elif out_fmt in ("ogg", "opus"):
            subprocess.run(
                ["ffmpeg", "-y", "-i", wav, "-c:a", "libopus",
                 "-b:a", "128k", "-ar", "48000", output_path],
                check=True,
            )
        else:
            subprocess.run(
                ["ffmpeg", "-y", "-i", wav, "-c:a", "libmp3lame",
                 "-q:a", "4", output_path],
                check=True,
            )

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
