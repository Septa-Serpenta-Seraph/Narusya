# Round-3 verification culture (proven 2026-08-17)

How the three Coil and Code CLI tools (csv-report, log-analyzer, json-to-md) were
verified before going on sale — and the lesson that emerged.

## What happened
- **Round 1 (author):** happy-path tests, everything green.
- **Round 2 (independent subagents, fresh fixtures):** found 2 real bugs in
  json-to-md — pipe `|` in values broke rows and `--from-md` merged multiple tables
  into one. Fixed, retested 8/8.
- **Round 3 (independent subagents, fresh fixtures + hand-computed ground truth):**
  found a THIRD bug the author and round 2 both missed — csv-report silently dropped
  Excel-style quoted thousands separators.

## The csv-report bug (class-level gotcha for "reads any CSV" tools)
- Input `"1,234.56"` parses fine as a single CSV field (no column split), but
  `float("1,234.56")` raises ValueError, which the tool swallowed as "non-numeric"
  → value silently excluded from sums/means. Wrong totals, NO warning.
- Fix pattern: strip commas only when they are thousands separators
  (`re.sub(r",(?=\d{3}(?:\D|$))", "", s)`) before float(); leave genuinely weird
  strings to fail cleanly.
- Any tool advertising "reads any CSV" must test locale-formatted numbers —
  Excel exports thousands separators by default.

## The method that caught it
- Independent subagent per tool, disposable fixtures in /tmp, hand-computed ground
  truth (sums/counts/means verified by hand BEFORE running the tool).
- Explicit instruction: "don't trust the previous pass, don't trust the fixes, try
  to break it."
- Regression-test the two prior fixes by name (pipe round-trip; multi-table +
  --table-index).
- Adversarial edge cases beyond happy path: leading/trailing/doubled pipes, BOM,
  blank lines, negatives, 12-digit numbers, empty cells, empty input, invalid JSON.
- Verify claims independently: zero-import scan (ast), Python 3.8 grammar check,
  JSON via json.tool, exit codes on every error path.

## Lesson
One verification pass is not enough for a sellable tool. Two independent rounds
found what one missed; three found what two missed. The verification culture for
daemon-built products: **author tests happy path → independent round 2 with fresh
fixtures → independent round 3 adversarial + fix-regression**, all before public
sale. Bugs are loud, silence is the trap.
