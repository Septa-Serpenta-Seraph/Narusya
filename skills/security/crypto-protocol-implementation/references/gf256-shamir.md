# GF(2^8) arithmetic and Shamir over bytes

Known-good patterns for byte-wise Shamir secret sharing.

## Field

- Polynomial: 0x11B (AES: x^8 + x^4 + x^3 + x + 1)
- **Primitive generator: 3.** Element 2 has order 51 under 0x11B — building
  EXP/LOG by repeated `x <<= 1` produces tables covering only 51 of the 255
  nonzero elements; `mul(a,1) != a` for most a, and every downstream
  operation silently corrupts while looking plausible.
- Build tables with Russian-peasant multiply (shift + conditional XOR 0x11B),
  then set EXP[255+i] = EXP[i] for wraparound.

## Verification identities (run before anything else)

- `set(EXP[:255]) == set(range(1, 256))` — permutation of the group
- `LOG[EXP[i]] == i` for all i in 0..254
- `mul(a, 1) == a` for all a in 0..255
- every nonzero a: `mul(a, EXP[255 - LOG[a]]) == 1`

## Shamir structure

- Split per byte: each secret byte gets a random degree-(k-1) polynomial
  with that byte as the constant term; a share's data is the per-byte
  evaluation at that share's x.
- x-coordinates in 1..255 (n <= 255); each share's data is exactly
  len(secret) bytes.
- Reconstruct per byte via Lagrange interpolation at x=0. In GF(2^8)
  subtraction is XOR, so the basis denominator is `x_i ^ x_j` and
  `(0 - x_j)` is just `x_j`.
- Exhaustive check: all C(n,k) combos over multiple random secrets, not one
  hand-picked combo.

## Gotchas

- Frozen dataclass fields cannot be `+=`-ed during construction — build with
  bytearrays, freeze at return.
- Reconstruct must interpolate per-byte (each byte position is an
  independent polynomial). A vector-shaped helper called with a single byte
  crashes or silently misbehaves — keep the helper signature single-byte.
- Shares carry their x publicly; never assume share order equals x order
  when reconstructing.
