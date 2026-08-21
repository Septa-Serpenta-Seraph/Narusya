# Product bug-hunt — 2026-08-20 (all five Coil & Code CLI tools)

Method: build gnarly fixtures that break naive tools, run EVERY advertised flag
of EVERY tool, cross-check docs vs actual parser, fix, rebuild zips, verify zip
contents, push. Add a test to a fixture file next time anything touches a tool.

## Fixtures that caught real bugs
- Dirty CSV: empty numeric cells, quoted commas inside fields (`"ordered, urgent"`,
  `"customer, vip"`), missing values, duplicate keys.
- Access log: real **Apache Combined format** (referrer + user-agent present).
- JSON: nulls (`score: null`, `tags: [null,"x"]`), nested objects, booleans,
  rows missing keys.
- Markdown: YAML front matter, headings inside code fences, `# not a heading`
  inside a table row, duplicate headings, punctuation-heavy headings.

## Findings & fixes
| Tool | Issue | Fix |
|------|-------|-----|
| log-analyzer | **Regex only parsed Common Log Format; docstrings/README claim Apache Combined (nginx default).** Real combined logs → `ERROR: no parseable lines (Apache Combined format expected)` — the tool couldn't read its own advertised format. | Made referrer/UA optional suffix: `r'... \d{3} (\S+)(?: "([^"]*)" "([^"]*)")?$'`; read groups with `m.lastindex` guard. Re-verified all modes (top-ips/paths/methods/status-errors/hourly/json). |
| csv-merge | **Silent data loss on duplicate keys**: a merge row with the same key overwrote the previous row (Adora's O-101 vanished when O-103 matched) — no warning. | Print `WARNING: duplicate key '<k>' in <file> — later rows collapsed (first match wins)` to stderr for dup keys in base AND merge files; first match wins; document in README. |
| csv-merge | Output had `\r\n` line endings via csv's default writer terminator (ugly on Unix). | `lineterminator="\n"` on both DictWriters (stdout + file). |
| csv-report | Docstring showed `--sort count desc`; parser only accepts `--sort {count,group}` → example fails. | Fixed docstring to `--sort count`. README was already correct — check docs-vs-parser on BOTH. |

## Clean tools (no bugs)
- json-to-md: round-trip (table → JSON), `--flatten` (NDJSON), `--table-index`
  multi-table extraction, `--columns` (documented as ORDER not filter — test
  that distinction), escaping of `|` in cells all correct.
- md-toc: GitHub slugify (`Usage`→`usage`, duplicate→`usage-1`, em-dash→`--`),
  skips YAML front matter + code fences + indented blocks, idempotent `--insert`
  (replaces its own `<!-- TOC -->` block).

## Release sequence mistakes to avoid
1. Rebuilt zips BEFORE all fixes were done once — always rebuild at the END.
2. Verified zips contain the fix string (zipfile.read().decode()) — do this,
   a stale zip silently ships the bug.
3. Git: made commits on `main` while `master` had the history → branch confusion,
   unrelated-histories merge needed, pycache junk committed. Sequence: commit on
   the working branch → checkout default → merge → push both.