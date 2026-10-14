# Library API shapes for crypto work

Inspect the live module before writing calls — shapes below are recorded for
the versions used, and drift is common across releases.

## Inspect-first pattern

```python
from cryptography.hazmat.primitives.asymmetric import mlkem
import inspect
print([a for a in dir(mlkem) if not a.startswith('_')])
# probe the expected entry point before committing to it:
_ = mlkem.MLKEM768.generate  # AttributeError here means the shape differs
```

## cryptography 50.0.1 (verified)

- **MLKEM768**: `mlkem.MLKEM768.generate()` (static, returns private key);
  `from_public_bytes(raw)` / `from_private_bytes(raw)`; public key:
  `public_bytes_raw()`, `encapsulate() -> (ciphertext, shared_secret)`;
  private key: `private_bytes_raw()`,
  `decapsulate(ct) -> shared_secret`. NOT constructor-wrapping —
  `MLKEM768(MLKEM768.PublicKey(...))` does not exist in this version.
- **X25519**: `X25519PrivateKey.generate()`,
  `from_private_bytes(seed)`;
  `X25519PublicKey.from_public_bytes(raw)`; `exchange()`.
- **AESGCM**: `encrypt(nonce, data, aad)`; `decrypt` raises `InvalidTag`
  on a wrong key — the clean negative-test signal for threshold crypto.
- **HKDF**: `HKDF(algorithm=SHA256(), length, salt, info).derive(ss)`.

## Capability detection

```python
try:
    from cryptography.hazmat.primitives.asymmetric import mlkem
    _ = mlkem.MLKEM768.generate
    _HAS_MLKEM = True
except (ImportError, AttributeError):
    _HAS_MLKEM = False
```

Catch AttributeError alongside ImportError — the module can import fine
while the expected entry points are absent or renamed.

## Composite key blobs

When carrying multiple key types as one blob (e.g. X25519 public key +
ML-KEM public key concatenated), document the byte layout in the module
docstring and slice by fixed offsets — the pattern works, but only if the
layout is written down where the next reader will find it.
