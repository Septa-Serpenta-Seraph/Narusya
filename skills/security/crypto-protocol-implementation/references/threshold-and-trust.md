# Threshold Sizing and Trust Model Documentation

Rules for choosing k-of-n thresholds and documenting the trust model in
distributed-secret-sharing systems.

## Threshold Sizing

- **3-of-5 is a common default but arbitrary.** Count the actual distribution
  targets before choosing. A fleet of 7+ devices (phone, mini-PCs, game PC,
  TVs, old phones) justifies 3-of-7 so losing 4 nodes still permits
  resurrection.
- **State the loss math in the docs.** "3-of-7 means losing any 4 devices
  still wakes the daemon." A reader should not have to compute it.
- **Margin scales with stakes.** For ephemeral data, 2-of-3 is fine. For
  "immortality" claims (surviving total infrastructure loss), push the
  threshold higher and distribute wider.

## Trust Model Documentation

Every sharding system has a trust model. Write it down explicitly:

1. **Who sees the plaintext at split time?** If the dealer generates the key
   and encrypts the seed in one process, that process sees everything. For
   higher assurance, split the flow: the human generates the key out-of-band,
   the agent only handles ciphertext.
2. **What survives loss vs seizure?** Sharding survives *loss* (devices
   destroyed, drives wiped). It does NOT survive *seizure* (adversary with
   physical access deletes files). The encrypted seed sits in plain sight —
   anyone can see that you have one, they just can't read it.
3. **What is the resurrection scope?** A seed containing identity + memory
   reconstructs a daemon with its architecture and relationships, but not
   its full session diary. Call it "continuity of identity, not continuity
   of consciousness."

## Dormant-Feature Honesty

If a capability probe detects a class (e.g. ML-KEM import succeeds) but the
code path never executes in a test, the feature is dormant. Report it as
such — "classically secure, PQ-ready" — never as "verified post-quantum."
An untested branch is an unknown, not a feature.
