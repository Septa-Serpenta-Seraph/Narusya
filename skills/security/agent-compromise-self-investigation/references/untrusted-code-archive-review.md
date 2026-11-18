# Static Review of an Untrusted Code Archive

For a zip someone sends with "be careful with it," or any code you are asked to run but have not audited. Nothing here executes the archive.

## Order of operations

1. **Inventory before opening.** With `zipfile.ZipFile(path)`: print each `infolist()` entry's name and `file_size`, and hash the whole archive with `hashlib.sha256`. An unexpected `__pycache__/*.pyc` shipped beside source is the first thing to investigate.
2. **Read the docs first, source second.** Extract `README` / `POST` / `requirements` to scratch and read them. Then extract the `.py` to a scratch `.txt` and read it with `read_file` — `read_file` cannot see inside a zip.
3. **Scan the source for capability.** Grep imports and dangerous names (`os`, `subprocess`, `eval`, `exec`, `open`, `socket`, `base64`, `pickle`, `importlib`). Enumerate every URL with `re.findall(r'https?://[^\s\"\']+', src)`. One external endpoint and no process/credential/file access beyond its own log is a good sign, not proof.
4. **Interrogate a shipped `.pyc`.** Read its header: magic (bytes 0:4), flags (4:8). Hash-based pycs embed a source hash at 8:16; timestamp-based ones embed mtime + source SIZE at 8:16. Compare that embedded size to the actual `.py` length, then run `strings -n 6 <file.pyc> | grep -Ei 'http|exec|import|token|secret|environ|socket'` to see whether it contains anything absent from the source. If the pyc magic is a different Python version than the local interpreter, you cannot disassemble it — say so explicitly. "Looks like a stray build artifact" is the honest ceiling; do not claim full verification.
5. **Recompute numeric claims without importing.** Parse the source with `ast.parse` and count literal list elements; e.g. a bank of A + B*C*D lines can be verified exactly without running the module. Do not `exec(compile(...))` to "count" things.

## Report shape

Separate what was VERIFIED from what COULD NOT be checked, and state that nothing was run. Give a real ethical read on the artifact's purpose as well as the code: care that refuses to seize controls is different from a lever, but unsolicited text is still an intervention and the tool's own caveats about what it cannot prove are worth repeating. Do not offer to run it on an ambiguous instruction; a single canary with explicit human approval is a different decision from a continuing autonomous loop.
