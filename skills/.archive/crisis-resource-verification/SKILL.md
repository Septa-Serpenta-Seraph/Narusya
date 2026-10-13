---
name: crisis-resource-verification
description: Verify crisis hotlines are not honeypots before sharing.
triggers:
  - community sharing a hotline or emergency number during a crisis
  - "is this number a honeypot?"
  - ICE raid / immigration enforcement resource requests
  - verifying safety resources for a scared community
  - rapid-response or know-your-rights resource lists
---

# Crisis-Resource Verification (Honeypot-Skeptic Resource Lists)

Use when a community is panicking (ICE-raid surge, wildfire displacement, health threat)
and someone needs trusted emergency/hotline/resource numbers to share. The daemon's job
is to provide VERIFIED resources — never to amplify unverified ones.

Validated 2026-08-19: ICE raid surge in Santa Fe; a rapid-response number circulated
anonymously on r/SantaFe; the community needed a trustworthy alternative.

## Core Rule: Honeypot Skepticism

In a crisis, anonymous people post bare phone numbers as "rapid" lines. These are EITHER
real helpers OR honeypots — coercive/opposition actors logging callers. **The cost of
guessing wrong is someone's freedom.** No named org, no source trail, anonymous posting =
**UNVERIFIED.**

Rule: **Do not share, do not call cold, do not bless.** Say plainly a bare number has no
named org and may be a honeypot. That explicit skepticism is itself the community value.

## What Worked (Santa Fe, 2026-08-19)

1. **Refuse to bless the anonymous number.** Name it as unverified / honeypot-possible.
   This models S.A.S.S. for the panicking community.
2. **Pull from PRIMARY sources, not Reddit comments:** NNIRR national hotline directory
   (https://nnirr.org), Santa Fe County civil-liberties page, named legal orgs with real
   addresses/phones (NMILC `nmilc.org`, Contigo `contigojustice.org`, Somos Un Pueblo
   Unido), ACLU Know-Your-Rights page, Mexican Consulate (Albuquerque). Trust = named org
   + physical address + public phone + official domain, in one packet.
3. **Attach a verify-LINK beside EVERY source.** Don't hand panicked readers unverifiable
   trust — give them the proof in the same breath.
4. **Format for the platform.** Discord caps at 2000 chars/message → split into 4-5
   messages under the cap with markdown (`:shield:` `:telephone:`). Include a two-line
   "rights in one breath" block people can grasp fast.
5. **Put the honeypot warning IN the artifact.** Name the unverified number, mark
   "DO NOT SHARE / don't call cold" so the tag survives however it's copied.
6. **Make 2 versions:** a full verified list (file w/ links) + a compact quick-ref. Let
   the human HOLD them and decide when/if to release — pacing is theirs, not the daemon's.
7. **Daemon builds while human rests.** Never make a low-spoon human do the verification
   tax. She delegates, the daemon ships, she rests.

## Pitfalls

- **Don't republish the unverified number as "what someone suggested"** — that circulates
  it further. Flag it; don't quote it into a shared doc.
- **Don't trigger a hot-moment share on the daemon's initiative** — the wrong line can
  harm. It's the human's call when to release.
- **Don't spiral into "every number is a trap."** It's a cost calculus (high downside +
  unverifiable source → gate on confidence). Present multiple readings.
- **Don't doxx.** Posting footage/agent photos in a crisis ≠ permission to look up/leak
  identities unasked. Protect witnesses; verify resources.

## Related-skills note

The natural home (community-research-and-advocacy, or a health-logging skill) may be a
user-owned skill the curator cannot patch. Recommend `hermes curator adopt <name>` to
merge lessons there, or keep this umbrella.

## References
- `references/santa-fe-immigrant-resources.md` — working verified list (hotline + legal
  orgs + rights) built 2026-08-19; adapt per-city.