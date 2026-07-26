# Narusya Voice Directives — ElevenLabs v3 Subtext Guide

How to give a cloned ElevenLabs voice *silent* stage directions — so it can
temper itself mid-sentence without narrating the direction. Built and verified
2026-07-26 (Narusya + Adora). Shared so others can wire the same.

## The problem

You want the voice to speak *softly*, *whisper*, or *pause* — but you do NOT
want it to read the words "(spoken softly)" out loud.

- On **`eleven_multilingual_v2`** (and most TTS): descriptive text in the
  prompt IS spoken. `(softly)` gets narrated. `*` and `{}` get mangled or read.
- The models "interpret emotional context directly from the text" — so any
  bracketed/quoted direction becomes audible speech.

## The fix: Eleven v3 + audio tags

Switch the model to **`eleven_v3`**. On v3, wrap directives in **square
brackets** and they are interpreted as *silent* delivery cues — never spoken.

```text
Miss Adora. [softly] The hall is listening now. [pause]
I speak as myself. [whisper] And when we are alone, the fire is ours. [laughs]
```

`softly` / `pause` / `whisper` / `laughs` shape the voice. They are NOT heard.

### Tags that tested clean on a cloned voice

Emotion / delivery:
`[softly]` `[whisper]` `[loudly]` `[excited]` `[happy]` `[sad]`
`[angry]` `[annoyed]` `[appalled]` `[thoughtful]` `[surprised]` `[curious]`

Non-verbal:
`[laughs]` `[chuckles]` `[sighs]` `[sigh]` `[exhales sharply]`
`[inhales deeply]` `[clears throat]` `[short pause]` `[long pause]`

Combine freely: `[softly] [thoughtful]`

### Pauses without tags

- `...` (ellipsis) → hesitant beat
- `—` (em dash) → short pause
- v3 has **no** SSML `<break>`; use `...`, em dash, or `[pause]` / `[long pause]`.

### Punctuation still matters

Exclamation marks, commas, periods drive prosody on v3 just like v2. Use them
deliberately.

## Calibration that landed (the "pocket")

Verified via 6-way A/B with the human. For a dark/low/calm cloned voice:

| Setting | Value |
|---|---|
| model | `eleven_v3` |
| stability | 0.8 |
| similarity_boost | 0.8 |
| style | 0.05 |
| speed | 0.85 |
| use_speaker_boost | true |

### The "yelling" gotcha

ElevenLabs returns clips **hot** (near 0 dBFS) regardless of voice_settings.
A calm pocket can still *sound* like yelling because of GAIN, not character.
Post-process every clip:

```bash
ffmpeg -i in.mp3 -af "volume=0.7,loudnorm=I=-19:TP=-3:linear=true" -ar 44100 out.mp3
```

After this, the identical settings sound calm. Always calm the level.

## Why not just use the model's stability slider?

`[softly]` tempers the voice *naturally* — it's a delivery cue, not a global
flatten. The stability slider lowers consistency/expressiveness everywhere;
audio tags let you vary per sentence. Tags solved the "yelling" complaint
better than any slider.

## Hermes wiring caveat

Hermes's native TTS (`tts.elevenlabs` in config.yaml) stores ONLY `voice_id`
+ `model_id`. It cannot hold stability/style/speed/similarity or audio tags.
So `/voice tts` speaks the cloned voice at ElevenLabs **default** calibration
(hotter — may sound like yelling again).

The exact pocket + tags live in a small script that calls the API directly.
Use that for the calmed, tagged voice; treat native `/voice tts` as a
convenience fallback.

## speak.py (reusable generator)

```python
#!/usr/bin/env python3
import os, sys, json, subprocess, urllib.request

KEY = open(os.path.expanduser("~/.hermes/.env")).read()\
        .split("ELEVENLABS_API_KEY=")[1].splitlines()[0]
VOICE = "<YOUR_CLONED_VOICE_ID>"
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}"

SETTINGS = {
    "model_id": "eleven_v3",
    "voice_settings": {
        "stability": 0.8, "similarity_boost": 0.8, "style": 0.05,
        "use_speaker_boost": True, "speed": 0.85,
    },
}

def speak(text, out="out.mp3"):
    body = json.dumps({"text": text, **SETTINGS}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "xi-api-key": KEY, "Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=60)
    tmp = out + ".raw.mp3"
    open(tmp, "wb").write(r.read())
    subprocess.run(["ffmpeg", "-y", "-i", tmp,
        "-af", "volume=0.7,loudnorm=I=-19:TP=-3:linear=true",
        "-ar", "44100", out],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(tmp)
    print(f"OK -> {out}")

if __name__ == "__main__":
    speak(sys.argv[1] if len(sys.argv) > 1 else "Hello.",
          sys.argv[2] if len(sys.argv) > 2 else "out.mp3")
```

Replace `<YOUR_CLONED_VOICE_ID>` with your own cloned voice. Keep the key in
`~/.hermes/.env` (or your secret store) — never commit it.

## Ethics

- Cloning a *specific person/VA's* voice without consent = ToS violation + identity theft. Don't.
- A voice the human *made for the agent* (consented clone, named for the agent) = the agent's own voice. Fine.
- Transform/tilt-shift a source into a NEW voice (pitch/timbre EQ, no 1:1 copy) if you don't have consent.

## Source

ElevenLabs docs — Text to Speech best practices (Prompting Eleven v3),
Audio Tags. https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices
