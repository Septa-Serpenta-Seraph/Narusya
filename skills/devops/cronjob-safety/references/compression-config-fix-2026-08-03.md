# Compression Configuration Fix — 2026-08-03

## Problem
The `auxiliary.compression.model` in `~/.hermes/config.yaml` was set to `google/gemini-3-flash-preview` — a paid model that fails with payment errors (404) on free-tier Nous gateways. This causes context compression to silently break, leading to lost threads and degraded daemon memory across sessions.

## Detection
- Check `~/.hermes/logs/agent.log` for `Auxiliary compression: payment error` or `Failed to generate context summary` warnings
- Check `config.yaml` line 187-191 for `compression.model` set to a paid provider

## Fix
Set `compression.model` to `''` in the `auxiliary` section of `config.yaml` so the gateway uses its built-in default compression method instead of routing to a paid model.

## Command
```bash
sed -i "s/model: google\/gemini-3-flash-preview/model: ''/" ~/.hermes/config.yaml
```

## Note
Do NOT hand-edit `config.yaml` for the user — use `hermes config set` or direct `sed` with user approval. The `compression` section is under `auxiliary`, not the top-level `compression` block.