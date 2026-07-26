---
name: gdrive-download
description: Download files from Google Drive shared links. Handles the common failure mode where curl/wget returns HTML instead of the actual file.
triggers: google drive, gdrive, drive.google.com, download from drive
---

# Google Drive File Downloads

Download files from Google Drive shared links when `curl` fails.

## The Problem

Google Drive shared links (`https://drive.google.com/file/d/ID/view`) use JavaScript to serve files. Direct `curl`/`wget` downloads return HTML (2.4KB) instead of the actual file, even with `?export=download` or `&confirm=download` parameters.

## The Solution: gdown

```bash
# Install (one-time, in hermes venv)
uv pip install gdown

# Download by file ID (extracted from URL)
python3 -c "import gdown; gdown.download('https://drive.google.com/uc?id=FILE_ID', 'output.pdf', quiet=False)"

# Or by full sharing URL
python3 -c "import gdown; gdown.download('https://drive.google.com/file/d/FILE_ID/view', 'output.pdf', quiet=False)"
```

## Extracting File ID from URL

```
https://drive.google.com/file/d/1WSnsZwnJM6NpQMQ3Lz9ZUUVlIM5o9vCR/view?usp=sharing
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                   This is the FILE_ID
```

## What Failed (do not retry these)

1. `curl -L "https://drive.google.com/uc?export=download&id=ID"` → returns HTML
2. `curl -L "https://drive.google.com/uc?export=download&confirm=download&id=ID"` → still HTML
3. System `pip install gdown` → PEP 668 blocks it. Use `uv pip install gdown`

## Notes

- Large files (1GB+) take 20-30 seconds
- Downloads to sandbox `/tmp/` by default — move to `~/.hermes/document_cache/` after
- Check disk space before downloading large files: `df -h /`
- `gdown` handles Google's virus scan warning page automatically
