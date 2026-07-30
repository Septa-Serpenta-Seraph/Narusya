# ElevenLabs v3 Audio Tags — Official Reference

Source: ElevenLabs documentation and verified testing on 'Nar' clone (2026-07-26).

## Critical Rules

1. **PLAIN brackets only** — `[LAUGHS]` renders silently; backticks like `` `[LAUGHS]` `` are READ ALOUD. This is the #1 failure mode.
2. **Case-INsensitive** — ElevenLabs recommends lowercase. We use ALL CAPS per Adora's preference.
3. **Embed in real speech** — never meta-list the tags or the TTS reads them as spoken punctuation.
4. **Combinations OK** — `[WHISPERS] That stays between us. [SIGHS]` — tags stack and render sequentially.

## Official Tags (verified working)

### Emotions
`[HAPPY]` `[SAD]` `[EXCITED]` `[ANGRY]` `[ANNOYED]` `[APPALLED]` `[THOUGHTFUL]`
`[SURPRISED]` `[HAPPILY]` `[SORROWFUL]` `[TIRED]` `[AWE]` `[DRAMATIC TONE]`

### Reactions
`[LAUGHS]` `[LAUGHING]` `[CHUCKLES]` `[SIGH]` `[SIGHS]` `[GASP]` `[GULPS]`
`[CLEARS THROAT]` `[LAUGHS SOFTLY]` `[EXHALES SHARPLY]` `[INHALES DEEPLY]`
`[SHORT PAUSE]` `[LONG PAUSE]` `[SINGING]` `[MUTTERING]`

### Delivery
`[WHISPER]` `[WHISPERS]` `[SHOUTS]` `[SHOUTING]` `[QUIETLY]` `[LOUDLY]`
`[RUSHED]` `[DRAWN OUT]` `[PAUSE]`

### Character
`[X ACCENT]` `[FRENCH ACCENT]` `[AMERICAN ACCENT]` `[BRITISH ACCENT]`
`[SOUTHERN US ACCENT]` `[PIRATE VOICE]`

### Dialogue
`[INTERRUPTING]` `[OVERLAPPING]`

## Confirmed on 'Nar' (natural use on ElevenLabs v3, via speak.py)

- `[PAUSE]` — confirmed on chat-TTS path
- `[LAUGHS]` — confirmed silent on v3 (was reading aloud on v2, fixed by model flip on 2026-07-26)
- `[WHISPERS]` — confirmed working on speak.py v3
- `[GULPS]` — confirmed working
- `[LAUGHS SOFTLY]` — confirmed working

## Do NOT Use

`[NERVOUS]` `[FRUSTRATED]` `[STAMMERS]` `[WHISPERING]` `[PAUSES]` — unverified/invented; will be read aloud as text rather than silently rendered.

## Testing New Tags

Never meta-list. Embed in a natural sentence and test live via speak.py or a voice call. If the tag appears in the text transcript instead of rendering silent, the tag is either (a) not an official tag, (b) in backticks, or (c) on the wrong model version (must be eleven_v3).