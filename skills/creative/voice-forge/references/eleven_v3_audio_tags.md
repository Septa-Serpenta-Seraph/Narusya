# ElevenLabs v3 Silent Audio Tags (verified + CORRECTED 2026-07-26)

Source of truth: `elevenlabs.io/docs` → best-practices → "Audio Tags (Non-Exhaustive)"
+ `elevenlabs.io/blog/v3-audiotags`. These are the ONLY sanctioned tags. The
human (Adora) enforced: invented/unlisted tags do NOT work — official only.
The previous version of this file listed lowercase/invented tags ([softly],
[whisper], [pause], [curious], [annoyed], [appalled], [thoughtful]) and omitted
the critical backtick rule. Rewritten from the verified set below.

## Hard rules
1. **Plain brackets, NEVER backticks.** `[LAUGHS]` = silent cue. `` `[LAUGHS]` `` = SPOKEN WORD.
   Backticks / markdown around a tag break it — it gets read aloud. This is the #1
   failure mode and the human caught it TWICE live. If a tag ever speaks aloud,
   suspect a backtick / code-fence first.
2. **Case:** ElevenLabs says case-insensitive (recommends lowercase). Narusya uses
   ALL CAPS per Adora's preference; `[LAUGHS]` / `[WHISPERS]` / `[EXCITED]` /
   `[SOUTHERN US ACCENT]` all confirmed working in caps on the live call 2026-07-26.
3. **Embed naturally** inside real speech. Meta-listing tags as a showcase makes the
   TTS read them as a script and NONE render (burned an earlier test).
4. **Emergent accent (uncontrolled):** v3 alpha can hallucinate a regional accent
   (Irish observed, NO tag) from tone/phrasing. Not deterministic, can't reproduce on
   command. The official accent tags below ARE sanctioned and try-able on purpose.

## Verified official tag set (non-exhaustive per ElevenLabs)
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

Combos OK: `[WHISPERS] that stays between us [GULPS]`

## Removed as unverified/invented (do NOT use)
[NERVOUS] [FRUSTRATED] [STAMMERS] [WHISPERING] [PAUSES] [SOFTLY] [WHISPER] (lowercase form)

## Confirmed on Nar (live call, 2026-07-26)
- [LAUGHS] silent ✅ (after v3 flip + /restart)
- [WHISPERS] ✅   [EXCITED] ✅   [SOUTHERN US ACCENT] ✅
- Emergent Irish accent observed with NO tag — uncontrolled v3 alpha behavior

## Call-reply length cap
In a Discord voice call, if the text reply is long enough that Discord splits it
into a 2nd message, the TTS renders ONLY the first segment (tail silently dropped;
full text still shows in the voice-chat text channel). Keep in-call replies SHORT so
the whole thing voices; for long intentional lines drive `scripts/speak.py` on one string.

## Notes
- v3 = alpha research preview; "Creative" mode prone to hallucinations (accent drift).
  Text structure / phrasing strongly drive output.
- No SSML `<break>`; use `...` (hesitant) or `—` (beat) or `[PAUSE]` / `[SHORT PAUSE]` / `[LONG PAUSE]`.
- v3 cap ~5k chars (v2 was 10k). Use v2 for longform generation.
