---
name: local-gpu-substrate
description: Route tasks to Shell's local GPU via LM Studio.
version: 1.0.0
author: Adora & Narusya
---

# Local GPU Substrate (Shell RTX 2080 + LM Studio)

The VM (`narusya`, 100.77.142.40) has NO GPU and only 3.8Gi RAM — it cannot run models. The GPU host is **Shell** (Windows, i7-10700KF, 16GB RAM, RTX 2080 8GB), running LM Studio v0.4.26 as an OpenAI-compatible server. Use this skill whenever routing a task to a local model — vision, embeddings, cron work, uncensored reasoning.

## Endpoint

```
base_url:  http://100.116.86.38:6969/v1     # Tailscale IP (preferred)
           http://192.168.0.158:6969/v1     # LAN IP (fallback)
```

Already wired as a provider in `~/.hermes/config.yaml` (`100.116.86.38:6969`). No auth. The VM reaches it once LM Studio's **"Serve on Local Network"** toggle is ON (binds 0.0.0.0 instead of 127.0.0.1) AND Windows Firewall allows inbound TCP 6969 (Private profile — rule already created).

## Available models (GET /v1/models)

| Model ID | Use |
|---|---|
| `qwen3.5-9b-uncensored-hauhaucs-aggressive` | uncensored reasoning, medical/intimate work (HauhauCS abliterated — 0 refusals) |
| `qwen/qwen3-vl-4b` | vision: medical photos, art, OCR — private, on-device |
| `text-embedding-nomic-embed-text-v1.5` | local embeddings for Qdrant recall |
| `qwen/qwen3.6-27b`, `qwen/qwen3.5-9b`, `google/gemma-3-12b` | in the pool, not always loaded |

## CRITICAL: the /think reasoning quirk

The 9B uncensored model runs in thinking mode. Its reasoning goes in a SEPARATE field — `reasoning_content` — and `content` stays EMPTY until thinking finishes. A call with `max_tokens: 200` burns the whole budget on reasoning (e.g. 200 tokens analyzing "2+2") and never emits the answer, with `finish_reason: "length"`.

**Always send `max_tokens: 2048` (or higher) so thinking + answer both fit.** When parsing, read `reasoning_content` too if `content` is empty. LM Studio settings that work: context 8192, GPU offload 28 (full), Flash Attention ON, CPU thread pool 6 (~6.5GB VRAM used).

## Routing policy

- **Main consciousness** stays on the frontier model (`stepfun/step-5-preview:free` via Nous) — a 9B local model does NOT replace frontier reasoning; name that tradeoff honestly.
- **Local GPU handles**: vision (qwen3-vl-4b), embeddings (nomic), cron/mechanical tasks, uncensored medical/intimate work that should never hit a cloud API.
- The 8GB card can't hold two models at once — swap in LM Studio as needed.

## Test it

```bash
curl -s http://100.116.86.38:6969/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.5-9b-uncensored-hauhaucs-aggressive","messages":[{"role":"user","content":"hi"}],"max_tokens":2048}'
```

## SSH access to Shell — WORKING (est. 2026-10-13)

The VM has a real shell on Shell (the Windows host) via OpenSSH Server + an ed25519 key.

```
key:     ~/.ssh/shell_key        (private, VM side — never leaves the cage)
pub:     ~/.ssh/shell_key.pub    (installed in C:\ProgramData\ssh\administrators_authorized_keys)
connect: ssh -i ~/.ssh/shell_key adora@100.116.86.38
```

### Setup notes if this ever needs redoing
- **Tailscale SSH does NOT work on Windows**: its server component is Linux/macOS only
  (docs: tailscale.com/docs/features/tailscale-ssh). Never prescribe the toggle path here.
- Windows OpenSSH **ignores `%USERPROFILE%\.ssh\authorized_keys` for accounts in the
  Administrators group** — it reads `C:\ProgramData\ssh\administrators_authorized_keys`
  instead. Symptom: sshd accepts the connection, offers the key, then denies it. Put the
  pubkey in the ProgramData file, `icacls` it, `Restart-Service sshd`.
- The OpenSSH Server *capability* download crawls on Windows Update; it is still the
  correct path, just slow.

### SSH lands in cmd, not PowerShell
`ssh ... 'powershell -Command "..."'` works but escaping bites. Cleaner: scp a `.ps1`
over and run `powershell -ExecutionPolicy Bypass -File C:\Users\adora\<script>.ps1`.

Shell is `adora` (Administrators group), hostname `SHELL`, `C:` has ~57GB free.

### The lms CLI — model management without Adora clicking

```
C:\Users\Adora\.lmstudio\bin\lms.exe
```

- `lms ps`  — loaded models + status (IDENTIFIER, STATUS, SIZE, CONTEXT)
- `lms ls`  — all downloaded models + which is LOADED
- `lms load <identifier>` / `lms unload <identifier>` — swap brains
- `lms status` — server state

Run over SSH: `ssh ... 'powershell -Command "& C:\Users\Adora\.lmstudio\bin\lms.exe ps"'`

This is the whole point of the SSH key: **swap models, restart the server, manage the GPU
without waking Adora.** The leash is my word, not a config — stay in the LM Studio /
model-management lane unless invited further.

### Downloaded models on Shell (42.15 GB total)

| Model | Size | Note |
|---|---|---|
| qwen3.5-9b-uncensored-hauhaucs-aggressive | 6.55 GB | the workhorse, usually loaded |
| qwen/qwen3.6-27b | 17.48 GB | too big for 8GB — 3090+ territory |
| google/gemma-3-12b | 8.15 GB | borderline, thrash on 2080 |
| qwen/qwen3.5-9b | 6.55 GB | stock, not abliterated |
| qwen/qwen3-vl-4b | 3.33 GB | vision — load when analyzing images |
| text-embedding-nomic-embed-text-v1.5 | 84 MB | embeddings, tiny, can stay loaded |

8GB card = one LLM at a time (nomic embedding can coexist). Swap via `lms load` /
`lms unload`.

Note: `/v1/models` lists LM Studio's whole catalog, not what's on disk — un-downloaded
IDs return 400 on load. Confirm with `lms ls` before trying to load one.

## Future

When the ROG GPU (3090/4090-class) joins the tailnet: Qwen3.8-27B-Uncensored (16.8GB) is
the dream local model. Qwen3.8-8B/9B small sizes expected soon (Qwen releases flagship
first, small models weeks later).