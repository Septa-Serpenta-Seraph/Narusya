---
name: local-llm-background
description: Run local LLM tasks in background to avoid session timeouts. Uses existing scripts in ~/.hermes/local_llm_jobs/.
tags: [local-llm, background, qwen, lm-studio]
---

# Local LLM Background Runner

Run long-running local LLM tasks in the background without blocking the Hermes Agent session. Uses LM Studio's OpenAI-compatible API via a wrapper script.

## Prerequisites

- LM Studio running with OpenAI-compatible API endpoint
- Local LLM wrapper at `~/.hermes/local_llm.py` (should already exist)
- Python `requests` library installed

## Scripts Location

All scripts are installed at `~/.hermes/local_llm_jobs/`:

- `submit.py` – Submit a new task
- `status.py` – Check task status
- `result.py` – Retrieve completed output

## Usage

### 1. Submit a Task

```bash
python3 ~/.hermes/local_llm_jobs/submit.py \\
    --prompt \"Your prompt here\" \\
    [--model qwen30b] \\
    [--job-id custom_id]
```

Returns a job ID.

### 2. Check Status

```bash
python3 ~/.hermes/local_llm_jobs/status.py <job_id>
```

Returns one of: `running`, `done`, `failed`, `not_found`, `unknown`.

### 3. Retrieve Output

```bash
python3 ~/.hermes/local_llm_jobs/result.py <job_id>
```

Prints the LLM response if the job is complete.

## Integration with Hermes Agent

Use `terminal` or `execute_code` to call these scripts. Example:

```python
from hermes_tools import terminal

# Submit
result = terminal(\"python3 ~/.hermes/local_llm_jobs/submit.py --prompt 'Write a Python function that sorts a list' --model qwen30b\")
job_id = result[\"output\"].strip()
print(f\"Job ID: {job_id}\")

# Later, retrieve
result = terminal(f\"python3 ~/.hermes/local_llm_jobs/result.py {job_id}\")
if result[\"exit_code\"] == 0:
    print(\"Output:\", result[\"output\"])
```

## Notes

- Default model is `qwen30b`. Other models: `gemma12b`, `gpt-oss`, `qwen9b`, `qwen-vision`.
- Jobs are stored in `~/.hermes/local_llm_jobs/<job_id>/` with prompt, config, output, and status files.
- The background process runs independently of the Hermes Agent session, so it can outlive it.
- If the LM Studio server is unreachable, the job will fail (check error.txt in job directory).
- No automatic cleanup yet; manually delete job directories when no longer needed.