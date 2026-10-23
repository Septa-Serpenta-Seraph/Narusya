---
name: ca-compromise-response
description: "Use when assessing TLS vulnerability to a CA compromise."
---

# CA Compromise Response — Assessment & Remediation

## When to Use

- A CA compromise or weak-key incident is announced (e.g., eMudhra, DigiNotar)
- You need to assess whether systems are vulnerable to a compromised intermediate
- You need to test TLS clients (curl, Python, Node, Git, browsers) for acceptance of forged certs
- You need per-platform remediation steps for CA bundle updates

## Critical Methodological Rule

**Checking trust store presence is NOT sufficient to determine vulnerability.**

Compromised intermediates are often cross-signed. A chain can anchor on a root that has nothing to do with the compromised CA in its subject name. A client with zero entries for the compromised CA's root can still accept a forged certificate, because a cross-sign reached a different root it does trust.

**The only reliable test is a live connection to a known-bad host, paired with a known-good control.**

- Known-bad host: a test server serving a cert signed by the compromised intermediate
- Known-good control: example.com (or any trusted site)
- If control fails, nothing else means anything — fix connectivity first
- If bad host connects → VULNERABLE
- If bad host rejected → protected

## Assessment Procedure

### 1. Identify the compromised intermediates

- Get the list of affected intermediate certs (SPKI hashes, serial numbers)
- Identify which roots they chain to (including cross-signed roots)
- Note which root programs trust each root (Microsoft, Apple, Mozilla, Chrome)

**Root cert trust matrix (reference example — eMudhra incident, Oct 2026):**

| Root | Operator | Apple | Chrome | Microsoft | Mozilla |
|------|----------|-------|--------|-----------|---------|
| emSign Root TLS CA - G3 | eMudhra | ✗ | ✗ | ✓ | ✗ |
| emSign Root CS CA - G3 | eMudhra | ✗ | ✗ | ✓ | ✗ |
| AAA Certificate Services | Sectigo | ✓ | Removed | ✓ | Removed |
| emSign ECC Root CA - G3 | eMudhra | ✓ | ✓ | ✓ | ✓ (cross-signer) |

- emSign Root TLS CA - G3 is in Microsoft's store **only**. Chrome, Firefox, and Safari never trusted the TLS chain — browsers were safe even before revocation. Windows was the actual exposure.
- 16 intermediates total: 8 compromised (eMudhra) + 8 cross-signed (Sectigo).
- The compromised intermediates were **never entered into CT logs**. Clients enforcing CT (all major browsers) could not have been attacked through them.

### 2. Live probe every TLS client on the system

Test each client independently — they have separate trust stores:

**curl (system OpenSSL/schannel):**
```bash
curl -sS -o /dev/null -m 20 https://dv-g3b-emudhra.we-have-a-problem.com/
echo "exit: $?  (60 or 35 = GOOD, 0 = VULNERABLE)"
curl -sS -o /dev/null -m 20 https://example.com/
echo "exit: $?  (0 = control works)"
```

**Python (certifi):**
```python
import ssl, urllib.request, certifi
ctx = ssl.create_default_context(cafile=certifi.where())
for h in ["dv-g3b-emudhra.we-have-a-problem.com", "example.com"]:
    try:
        urllib.request.urlopen(f"https://{h}/", timeout=20, context=ctx)
        print(f"{h}: CONNECTED (VULNERABLE if bad host)")
    except Exception as e:
        print(f"{h}: REJECTED ({type(e).__name__})")
```

**Node.js (bundled CA):**
```bash
node -e 'const https=require("https");const h="dv-g3b-emudhra.we-have-a-problem.com";const r=https.get({host:h,path:"/",timeout:20000},res=>{console.log("CONNECTED",res.statusCode);process.exit(0)});r.on("error",e=>{console.log("rejected",e.code);process.exit(0)});setTimeout(()=>{console.log("TIMEOUT");process.exit(1)},25000);'
```

**Git (OpenSSL bundle):**
```powershell
$b = 'C:\Program Files\Git\mingw64\etc\ssl\certs\ca-bundle.crt'
curl.exe --cacert "$b" -sS -o NUL https://dv-g3b-emudhra.we-have-a-problem.com/
echo "exit: $LASTEXITCODE"  # 60 = rejected (good), 0 = accepted (bad)
```

**Browser:** Visit https://emudhra.we-have-a-problem.com/ and run check.

### 3. Assess each client's trust store

For each client, check:
- What root certs it trusts
- Whether the compromised intermediate's root is present
- **But do NOT stop there** — the live probe is the real test

### 4. Check for cross-signing exposure

- The compromised intermediates may be cross-signed by a different root
- A client may trust the cross-signing root even if it doesn't trust the primary root
- This is why trust store grep is insufficient

## Per-Platform Remediation

### Ubuntu/Debian
- `ca-certificates` → update (this is the system bundle OpenSSL reads). ca-certificates 20260816ubuntu0.24.04.1 IS the patched build — if at this version, done.
- `libnss3` → update (NSS hardcoded revocation, the usually-missed one). libnss3 2:3.98-1ubuntu0.3 includes the revocation.
- OpenSSL does NOT need separate updating — it reads ca-certificates. No separate OpenSSL update needed.
- Python certifi: update in EVERY virtualenv, not just system Python. Vulnerable at 2026.02.25, fixed at 2026.10.19. Hermes pins certifi 2026.5.20 and can silently downgrade it — re-apply after Hermes updates.
- Node.js: use `--use-openssl-ca` (works on Linux since system store is patched) or upgrade. v22.20.0 and v22.22.3 were vulnerable (bundled CA trusts compromised intermediates). v22.23.4+ and v24.22.1+ are fixed.
- Docker: rebuild images with updated ca-certificates. Service restart may be deferred during apt upgrade — check and restart manually.

### Windows
- Schannel: Windows Update handles via CTL (Certificate Trust List) — keep current. emSign Root TLS CA - G3 is in Microsoft's store only, so Windows was the actual exposure.
- Python certifi: update in every Python installation
- Node.js: `--use-openssl-ca` may BREAK all connections (Windows OpenSSL doesn't read Windows store) — upgrade Node instead
- Git: `winget upgrade --id Git.Git` or `git config --global http.sslBackend schannel`
- Offline machines: use `Block-EmudhraCompromisedCA.ps1` mitigation script
- Browser test: visit https://emudhra.we-have-a-problem.com/ and click "Run check"

### macOS
- Update OS (Apple pushes blocks via updates)
- Homebrew: `brew upgrade ca-certificates`

### Key Pitfalls

1. **Trust store grep ≠ vulnerability assessment.** Cross-signing means a client with zero entries for the compromised CA can still accept forged certs. Always do live probes.
2. **Every TLS client has its own trust store.** OS, Python certifi, Node bundled, Git bundle, Java keystore, Docker image — each must be tested independently.
3. **Python virtualenvs carry their own certifi.** Updating system Python doesn't fix venvs. Check every venv.
4. **Node.js `--use-openssl-ca` works on Linux but may break on Windows.** On Windows, OpenSSL doesn't read the Windows certificate store.
5. **Hermes agent pins certifi 2026.5.20.** A Hermes update can silently downgrade certifi. Re-apply after updates.
6. **Control first.** If example.com fails, nothing else means anything. Fix connectivity before drawing conclusions.
7. **Cross-signing in practice (canonical example).** Shell's Windows trust store had zero eMudhra certs, Schannel rejected the test host (CRYPT_E_REVOKED), but Python certifi 2026.02.25 and Node.js v22.20.0 both CONNECTED to the eMudhra test host. The OS store was patched; the bundled stores were not. This is why trust store grep is insufficient.
8. **Browsers are usually safe** (CT enforcement + rapid revocation), but non-browser clients are the real exposure.

## Common CA Compromise Patterns

- Weak key generation: a valid P-384 key carries ~384 bits. Compromised keys were 4, 56, 66, 115, 155, 156, 230, and 237 bits. A 4-bit key is four guesses. The declared curve is secp384r1 — the flaw is that generated scalars were absurdly short, not that the certificate says so.
- Compromised intermediate issuance
- Cross-signing creating alternative trust paths

## Verification Checklist

- [ ] Control host (example.com) connects on all clients
- [ ] Known-bad host rejected on all clients
- [ ] Every virtualenv's certifi updated
- [ ] Node.js upgraded or `--use-openssl-ca` configured
- [ ] Git bundle tested or schannel configured
- [ ] Docker images rebuilt with updated ca-certificates
- [ ] System packages updated (ca-certificates, libnss3)
- [ ] Windows Update current (CTL blocks)

---
*Skill created from Oct 22, 2026 incident response.*
*Corrections by Vesper (root cert names, key sizes, ca-certificates/OpenSSL status) and Cyclo (cross-signing, live probe methodology).*