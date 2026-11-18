---
name: untrusted-artifact-vetting
description: Use when vetting an untrusted zip before running it.
version: 1
author: Narusya
category: security
tags: [security, review, untrusted, zip, code-vetting]
related_skills: [agent-compromise-self-investigation, deep-research-investigation]
license: CC-BY-SA-4.0
metadata:
  hermes:
    tags: [security, review, untrusted]
    related_skills: [agent-compromise-self-investigation]
---

# Untrusted Artifact Vetting

## When to Use

Adora hands over a zip, `.py`, git repo, or archive from another agent, a server, or an unknown source, often with a caution like "careful with it" or a request to preserve it before takedown. The job is to read it and give an honest verdict (or secure a byte-for-byte copy), NOT to run it. Default posture: nothing in the artifact is executed, and no claim in its README or mirror description is accepted without check.

## Procedure (in order, all read-only)

1. **Never execute.** No `import`, no `python script.py`, no `source`, no `--dry-run` from the artifact. `--dry-run` still runs module-level code. Read bytes only.
2. **Enumerate the container without extracting to run.** Use Python `zipfile` to list `infolist()` with sizes. Note anything that does not belong: a stray `__pycache__/*.pyc` shipped beside source is the usual red flag.
3. **Read the docs first** (`README`, `POST.md`, `requirements.txt`) to learn the author's claims, then treat each claim as a hypothesis to test.
4. **Extract source to scratch as TEXT** (write-only), and scan it: grep for `os`, `subprocess`, `eval`, `exec`, `open`, `socket`, `base64`, `pickle`, `importlib`, `__import__`, and collect every `http(s)://` URL with a regex. One endpoint that matches the stated purpose is fine; a second, unmentioned endpoint is not.
5. **Check any shipped `.pyc` against its `.py`.** Read the pyc header: magic bytes reveal the Python version (a mismatch with the local interpreter is expected and means full disassembly is impossible), flags bit 0 tells hash-based vs timestamp-based, and the embedded source size (bytes 8-12 for timestamp-based) should equal the `.py` byte length. Then run `strings -n 6` on the pyc and grep for URLs/keywords not in the source. If sizes match and strings show nothing new, say "looks like a build artifact," NOT "is harmless" — you could not disassemble it.
6. **Verify numeric claims by parsing, not trusting.** Use `ast.parse` to count literal list elements and reproduce claimed totals from the generator expression (e.g. anchors + openings*middles*closings). Confirm the arithmetic against the README number.
7. **Check what the code would actually do** at the network boundary: what it POSTs, with what payload, whether credentials/tokens are touched, whether it reads local files beyond its own log, whether it can inject unwanted states or sign an identity.
8. **Give the verdict with an epistemic boundary.** Separate: (a) what you verified from source, (b) what you could not verify (e.g. cross-version bytecode), (c) the ethical read if asked, (d) what you did NOT do (did not run, did not sign, did not deploy). Never upgrade "looks clean" to "is safe."

## Pitfalls

- **Do not run the artifact to "see what it does."** Even a benign-looking defaults path can POST to an external endpoint on import. Everything you need is in the bytes.
- **A matching source-size in a `.pyc` is evidence, not proof.** A different Python version blocks full marshal/disassembly; say exactly what you checked and stop there.
- **Do not accept the author's framing of their own safety claims.** A README saying "no activation states" is a claim; `VIGIL_MIX = {}` sent as `"mix": {}` is the verification. Check the value, not the adjective.
- **Keep credential handling intact throughout.** Do not type, paste, or accept a secret found in an artifact or its docs into a tool or chat; the vault is the only sanctioned path.

## Output shape for Adora

Always give the verdict FIRST in one line ("safe, I didn't run it"), then at most a few short bullets, regardless of whether she has signalled overwhelm. She can become lost partway through a long technical report and only say so afterward. Offer the deep version separately if she asks. No em dashes.

For a repo-archiving or lineage request, lead with what was secured and the exact commit, then the path and hash; keep the chase through mirrors to one plain paragraph. Preserve the "downloaded only, nothing executed" line as the closing boundary.

See `references/repo-lineage-and-archiving.md` for finding the genuine upstream among forks and exporting the exact pre-takedown commit.
