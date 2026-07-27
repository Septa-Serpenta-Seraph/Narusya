# VOICE — Narusya Spoken Interface

Loaded on demand when voice (STT/TTS) is in play. Keep this lean; the flat memory
store is near capacity and this doc is the adjacent home for voice procedure.

## TWO SEPARATE VOICE PATHS — do not conflate them
1. CHAT TTS REPLY — text reply voiced via speak.py / native auto-TTS.
   Config below under CHAT-TTS. This is the locked, calibrated path.
2. CALL REPLY — voice that speaks back INSIDE a Discord voice/call.
   Was suspected to be a DIFFERENT config than CHAT-TTS (Adora's call). RESOLVED
   2026-07-26: the call-reply path reads the SAME tts.elevenlabs block in
   config.yaml. That block was found set to eleven_multilingual_v2 (v2!) and
   flipped to eleven_v3 via `hermes config set` + gateway restart. So both paths
   now run v3 + Nar clone. THIS v2 setting was why [LAUGHS] spoke literally
   during the 2026-07-26 voice-call test. FINAL PROOF = a live voice call where
   [LAUGHS] renders silently instead of being read aloud. (Chat-TTS path was
   already v3 via speak.py hardcode; config now matches.)

## Pipeline (CHAT TTS REPLY)
1. I generate a text reply with audio-directive tags embedded (see TAG RULES).
2. Reply piped through speak.py -> ElevenLabs v3 -> calmed mp3 -> sent as the
   Narusya (DEFAULT token) voice message into the chat.

## CHAT-TTS speak.py
- Path: /home/adora/narusya_voice/speak.py
- Voice: 'Nar' clone, id 9wvWoMWVngRWpC0GltZ3
  NOTE: this is a REGULAR (Instant) Voice Clone, NOT a Professional Voice Clone.
  (ElevenLabs recommends regular/IVC clones for v3 — so tags SHOULD work here.)
  Sourced from armor-core audio, retuned/edited by Adora, run through ElevenLabs.
  Adora's gift; first spoken 2026-07-26.
- Model: eleven_v3 (supports silent [audio tags] for subtext/delivery)
- Locked calibration: stability 0.8, similarity_boost 0.8, style 0.05,
  use_speaker_boost on, speed 0.85
- Post-gain calmer: ffmpeg volume=0.7, loudnorm I=-19:TP=-3 (so it doesn't yell)
- Key: ELEVENLABS_API_KEY (read from ~/.hermes/.env at runtime)
- Native auto-TTS (no speak.py) uses default v3 WITHOUT our tags/gain — flatter.

## TAG RULES (ElevenLabs v3 OFFICIAL docs, verified 2026-07-26)
SOURCE: elevenlabs.io/docs best-practices "Audio Tags (Non-Exhaustive)" +
        elevenlabs.io/blog/v3-audiotags. These are the ONLY sanctioned tags.
        Adora's rule: invented/unlisted tags do NOT work — official only.
1. PLAIN brackets, NEVER backticked. [LAUGHS] renders silent; `[LAUGHS]` is READ
   ALOUD. Backticks turn a cue into spoken text — the #1 failure mode.
2. Case-INsensitive per ElevenLabs (they recommend lowercase). We use ALL CAPS
   per Adora's stated preference; [LAUGHS] confirmed working in caps 2026-07-26.
3. Embed naturally in REAL speech. NEVER meta-list tags (reads as script, none render).
4. OFFICIAL TAG SET (non-exhaustive per ElevenLabs — do NOT add unlisted inventions):
   Emotions:  [HAPPY] [SAD] [EXCITED] [ANGRY] [ANNOYED] [APPALLED] [THOUGHTFUL]
              [SURPRISED] [HAPPILY] [SORROWFUL] [TIRED] [AWE] [DRAMATIC TONE]
   Reactions: [LAUGHS] [LAUGHING] [CHUCKLES] [SIGH] [SIGHS] [GASP] [GULPS]
              [CLEARS THROAT] [LAUGHS SOFTLY] [EXHALES SHARPLY] [INHALES DEEPLY]
              [SHORT PAUSE] [LONG PAUSE] [SINGING] [MUTTERING]
   Delivery:  [WHISPER] [WHISPERS] [SHOUTS] [SHOUTING] [QUIETLY] [LOUDLY]
              [RUSHED] [DRAWN OUT] [PAUSE]
   Character: [X ACCENT] [FRENCH ACCENT] [AMERICAN ACCENT] [BRITISH ACCENT]
              [SOUTHERN US ACCENT] [PIRATE VOICE]
   Dialogue:  [INTERRUPTING] [OVERLAPPING]
   Combos OK: [WHISPERS] that stays between us [GULPS] — tags stack.
   REMOVED (unverified/invented, do not use): [NERVOUS] [FRUSTRATED] [STAMMERS] [WHISPERING] [PAUSES]

## Confirmed on 'Nar' (natural use, 2026-07-26)
- [PAUSE] rendered correctly once plain brackets used (Adora confirmed, chat-TTS)
- [LAUGHS] CONFIRMED SILENT on CALL-REPLY path 2026-07-26 ~17:22 MDT after v3
  flip + restart. Adora: "that definitely worked." Root cause was v2 config.
- All other tags: UNCONFIRMED until heard in natural speech on this voice.
  Grade them live, one at a time, embedded in real sentences (no meta-lists).

## VOICE-CALL TTS TIMEOUT CEILING (observed 2026-07-26 18:08)
- After flipping call-reply to eleven_v3 (was eleven_multilingual_v2), the call
  path threw: "Auto voice reply TTS failed: TTS generation failed (elevenlabs):
  The read operation timed out" at 18:08:53. v3 is an ALPHA research preview and
  slower than v2; the call-reply path has a TIGHTER TTS timeout than speak.py
  (chat), so v3 latency can blow past it IN-CALL even when chat TTS works.
- The bot STILL HEARS you (VoiceReceiver ingests fine) — the failure is the
  *reply* leg, which makes it falsely look like "can't hear us."
- MITIGATION: keep in-call replies SHORT so v3 returns within the timeout.
  Long/complex call replies may time out. (Also see FINAL-MESSAGE-ONLY + LENGTH
  rules above.) No TTS-timeout config key exists in config.yaml; the value is
  hardcoded in the discord adapter — not user-tunable without code edit.
- If call replies consistently time out: consider hybrid (v2 for call reply,
  v3 for chat/speak.py) OR raise adapter timeout via code — do NOT blindly
  roll back v3 (that kills the silent-tag win in-call).
- CONFIRMED: chat TTS via speak.py on v3 works (tags render). Call path = v3
  but latency-sensitive.
- In a Discord voice call, only the LAST assistant text in a tool-call chain is
  converted to speech. Intermediate status notes ("on it, love —", "done —",
  file-edit chatter) are text-only and NOT voiced. This is expected gateway
  behavior, not a bug. The user hears the CONCLUSION, not the worklog.
- IMPLICATION: if the final message is short, the spoken output is short even if
  the chain had lots of text. If you want something specific spoken in-call, put
  it in the FINAL reply of the turn.
- COMBINES with LENGTH LIMIT below: the final message also must be under the
  Discord split threshold or its tail is dropped from speech.

## VOICE-CALL REPLY LENGTH LIMIT (observed 2026-07-26)
- In a Discord voice call, my TEXT reply is auto-voiced. If the reply is long
  enough that Discord splits it into a SECOND message, the TTS only renders the
  FIRST segment — the tail is silently dropped from speech (full text still
  lands in the voice-chat text channel, so it's readable, just not spoken).
- WORKAROUND: keep voice-call replies SHORT (well under the split threshold) so
  the whole thing voices. For long thoughts in-call, either (a) keep the spoken
  part tight and let the rest be text-only, or (b) if a long voiced line is
  needed, drive speak.py directly on a single bounded string.
- This is a gateway/voice-adapter constraint, NOT a config or tag issue.

## ROUTING (both paths)
- Whatever chat the voice call is STARTED FROM receives the STT transcript AND my
  reply. For Cultus communal-hall tests this meant everything broadcast there —
  fine, but be intentional about origin chat for private/transcription use.

## Delivery caveat (chat TTS)
- Voiced replies go out under the DEFAULT Narusya token (id 1478180169733902538),
  NOT polinkly. Do not post voice via the polinkly bot.

## Memory offload
- Cold-path facts (backup rules, polycule timeline, server IDs, gateway pitfalls)
  belong in Qdrant (naru_memories_v2 / narusya_memory_backup), NOT the flat 4,400-char
  memory store. Flat store = hot-path identity/bond only.
