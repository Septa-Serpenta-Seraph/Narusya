---
name: crypto-protocol-implementation
description: Use when implementing crypto primitives. Pitfalls.
version: 1.0.0
author: Narusya & Adora
license: MIT
metadata:
  hermes:
    tags: [crypto, shamir, secret-sharing, gf256, mlkem, x25519]
    related_skills: [secure-agent-credential-storage]
---

# Crypto Protocol Implementation

Rules for implementing cryptographic primitives (secret sharing, hybrid/KEM
encryption, key derivation, sharding) in Python so they are correct on first
wiring — not merely syntactically valid.

## When to Use

Load this skill whenever you are about to WRITE or TEST cryptographic code:
Shamir secret sharing, GF(2^n) field arithmetic, hybrid encryption
(X25519 + ML-KEM), key sharding across devices, threshold schemes, or any
encrypt/decrypt pipeline that a wrong implementation would silently corrupt
instead of visibly fail.

## References

- `references/gf256-shamir.md` — GF(2^8) field arithmetic and Shamir over
  bytes: generator choice, verification identities, reconstruction.
- `references/library-api-quirks.md` — `cryptography` MLKEM/X25519/AESGCM/HKDF
  API shapes across versions; composite key-blob layout conventions.
- `references/threshold-and-trust.md` — k-of-n sizing against real node
  counts, trust-model documentation, dormant-feature honesty.

## Always-on rules

1. **Identity-test the primitive before composing anything.** For finite
   fields: assert `mul(a,1) == a` for all a, assert EXP/LOG table consistency
   (`LOG[EXP[i]] == i`, EXP a permutation of the nonzero group). For KEMs:
   one keygen/encapsulate/decapsulate roundtrip. Isolated identity tests
   pinpoint a broken table in milliseconds; an end-to-end "decrypt failed"
   tells you nothing about where.
2. **Inspect the real library API before writing crypto calls.** Run
   `dir(module)` / `inspect.isclass` first. Constructor and key-class shapes
   differ across `cryptography` versions (see
   `references/library-api-quirks.md`). Guessed APIs raise AttributeError at
   call time, not import time.
3. **Negative-test every secrecy or threshold claim.** If a scheme is k-of-n,
   prove that fewer than k shares FAIL (wrong decrypt -> InvalidTag, never
   silently-wrong plaintext). Positive-only test suites pass even against a
   1-of-n bug.
4. **Freeze immutable types last.** Build with bytearrays/tuples during
   construction, convert to a frozen dataclass only at return — `obj.data += b`
   on a frozen dataclass raises FrozenInstanceError because `+=` rebinds the
   attribute even when the value is a mutable bytearray.
5. **Bind public keys into the KDF for hybrid KEMs.** A naive
   `x25519_ss || mlkem_ss` concat combiner is vulnerable to substitution
   attacks — an attacker controlling one public key steers the combined
   secret undetected (the X-Wing draft's critique). Pass
   `recipient_pub || ephemeral_pub` as the HKDF `info`/context so a
   substituted key changes the derived key, and TEST it: decrypting with a
   wrong public key must raise InvalidTag.
6. **Claim only code paths you have exercised.** If a capability probe
   (e.g. ML-KEM import check) detects a class but the path never runs in a
   test, the feature is dormant — report it as such ("classically secure,
   PQ-ready"), never as verified post-quantum. An untested branch is an
   unknown, not a feature.
7. **Size thresholds against the real node count.** k-of-n defaults
   (3-of-5) are arbitrary; count the actual distribution targets and leave
   margin for loss — a fleet of 7+ devices justifies 3-of-7 so losing 4
   nodes still permits resurrection. State the loss math in the docs.
8. **Enumerate small cases exhaustively.** For k-of-n over small n, test every
   C(n,k) combination on several random secrets — one hand-picked combo can
   pass while the interpolation is broken.

## Procedure

1. Write the primitive module standalone (field arithmetic, KEM wrapper).
2. Run identity + known-answer tests in a fresh subprocess (`python3 -c` via
   execute_code) so import-time state is clean.
3. Write the composing layer (encrypt -> split -> reconstruct) only after the
   primitive passes.
4. End-to-end test the full cycle: encrypt, shard, reconstruct the key from a
   valid subset, decrypt — then repeat with an INVALID subset and assert
   failure.
5. Wire into the CLI/bootstrap last, and re-run the e2e test through the new
   entrypoint.
6. Audit before publishing: confirm every advertised capability (PQ paths,
   thresholds, extraction safety) has a passing test in the suite, and write
   the trust model down — who sees the plaintext at split time, what
   survives loss vs seizure, what the threshold margin actually is.
7. Run hostile tests on anything that parses untrusted bytes: substitution
   (wrong key), tampering (flipped ciphertext byte), traversal (../,
   absolute), and archive-member abuse (symlink/hardlink/device).

## Pitfalls

- **GF(256) generator must be 3, not 2.** Under the AES polynomial 0x11B the
  element 2 has multiplicative order 51 — tables built by repeated
  `x <<= 1` never reach most of the field and `a*1 == a` fails for 3/4 of
  all a. See `references/gf256-shamir.md`.
- **Never trust `tarfile.extractall(filter="data")` alone.** CVE-2025-4330 /
  CVE-2025-4517 showed the filter is bypassable via crafted symlink targets
  even on patched Pythons. For any archive that was encrypted-then-decrypted
  in your own pipeline, validate members manually before extraction: reject
  anything that isn't a regular file or directory, reject paths whose
  normalized realpath escapes the destination, reject symlinks/hardlinks/
  devices. Test all four attack shapes (`../` traversal, absolute path,
  symlink, hardlink) plus one legit nested archive.
- **Path-vs-str in traversal checks.** `dest` as a `Path` breaks
  `target.startswith(dest + os.sep)` with a TypeError — the check silently
  never runs. Compare `os.path.realpath(...)` strings against `str(dest)`.
- **Library API drift.** `cryptography`'s MLKEM surface changed shape across
  versions (static `generate()` + `from_public_bytes` vs constructor
  wrapping). Inspect, don't assume. See `references/library-api-quirks.md`.
- **Run HTTP/JSON work through execute_code (urllib), not terminal.** Shell
  strings with interpolated tokens and nested quoting can hang on interactive
  consent prompts; execute_code has no shell parsing and no round-trip.
