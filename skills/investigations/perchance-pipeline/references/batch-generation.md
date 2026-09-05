# Batch Generation via the Perchance Driver (verified 2026-09-03)

The CLI driver `~/.hermes/imagegen/perchance-image.py` was extended with **true batch
mode** so a whole set of generations costs ONE browser launch + ONE Turnstile pass,
instead of relaunching Camoufox per image. Full session detail behind the summary in
SKILL.md.

## Flags

```bash
# N copies of one prompt, one browser session
.../perchance-image.py "prompt" --batch 4 portrait

# a .txt file of prompts, one per line (# = comment, blank lines skipped)
.../perchance-image.py --prompts prompts.txt portrait

# explicit multi-prompt list on the CLI
.../perchance-image.py --prompts "prompt A" "prompt B" "prompt C"

# custom output dir
.../perchance-image.py --prompts "p1" "p2" --outdir /path/to/dir

# single image (backward compatible, unchanged)
.../perchance-image.py "prompt" [portrait|square|landscape] [outdir]

# requires camoufox in the Hermes venv
~/.hermes/hermes-agent/venv/bin/python3 ...
```

## How it works

- `run_batch(prompts, shape, outdir)` opens ONE `AsyncCamoufox` browser, loads the
generator page once, and loops the prompt list: re-find the visible textarea,
fill, click generate, poll all frames for a fresh `data:image/{jpeg,png};base64,`
blob, decode + save.
- The textarea and generate button are **re-found before every generation** because
the page re-renders between outputs.
- Per-item timeout does NOT abort the batch — it logs a WARN and continues. Exit
code 0 if every prompt saved, 2 if partial (so a cron/backend can detect a drop).

## Gotchas (all hit for real 2026-09-03)

1. **Do NOT pass a trailing shape arg right after `--prompts`.**
   `perchance-image.py --prompts file.txt portrait` silently swallows `portrait` into
the prompt list, producing a garbage prompt (a literal single-char "prompt").
With `--prompts file.txt` + a trailing shape it also briefly produced junk files.
   Default shape is already `portrait` — just omit the trailing arg in batch mode.
2. **`args.prompts` is a LIST even when it holds one file path.** The first buggy cut
sent the whole list to `open()`, dying with
`TypeError: expected str, bytes or os.PathLike object, not list`. Fix: check
`len==1 and endswith('.txt')` then `open(args.prompts[0])`.
3. The readable prompt file format is the reliable batch input — write prompts (with
`#` comment lines) to a `.txt`, pass the file, and read back the counts before firing
(`grep -vcE '^\s*#|^\s*$' file.txt`) so you know exactly how many images to expect.

## 10-image gallery run (2026-09-03)

A 10-prompt character-variant gallery (5 versions of a character, 2 each) ran clean
in a SINGLE session after the two bugs above were fixed, saving all 10 files with the
right prompts. Confirm a healthy run by polling the process: it logs
`[*] batch N/10: generating...` then `[+] saved <path>` per item — you can watch the
correct count (`N/10`) in real time instead of trusting it finished.

## Prefer over shell-looping

Never `for p in prompts; do perchance-image.py "$p"; done` in a shell for, e.g., 10
genrations — that is 10 browser launches / 10 Turnstile passes and ~10x slower.
Always hand the driver the whole batch via `--batch` / `--prompts`.
