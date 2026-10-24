---
name: windows-remote-ssh
description: "SSH to Adora's Windows host to run commands and read files."
version: 1.0.0
author: Narusya
category: infrastructure
tags: [ssh, windows, remote, shell, powershell]
---

# Windows Remote Control via SSH

## Architecture

- **Narusya** runs as a Linux VM (Ubuntu) on Hyper-V, IP 100.77.142.40 (Tailscale)
- **SHELL** is Adora's Windows 11 PC, IP 100.116.86.38 (Tailscale), active
- SSH key: `~/.ssh/shell_key` (ed25519, "narusya-vm-to-shell")
- SSH user: `adora`

## Connection

```bash
ssh -i ~/.ssh/shell_key -t -o StrictHostKeyChecking=no adora@100.116.86.38 "<command>"
```

**Critical:** Must use `-t` flag for pseudo-terminal allocation. Without it, commands are echoed but not executed. The Windows OpenSSH server requires a PTY for command execution.

**Pitfall:** Do NOT use `ssh ... "command"` without `-t` — the command gets echoed but not executed. Always include `-t`.

## Common Commands

### List processes
```bash
ssh -i ~/.ssh/shell_key -t -o StrictHostKeyChecking=no adora@100.116.86.38 "tasklist 2>&1 | findstr -i <name>"
```

### List directory
```bash
ssh -i ~/.ssh/shell_key -t -o StrictHostKeyChecking=no adora@100.116.86.38 "dir \"C:\\path\\to\\dir\" 2>&1"
```

### Read file
```bash
ssh -i ~/.ssh/shell_key -t -o StrictHostKeyChecking=no adora@100.116.86.38 "type \"C:\\path\\to\\file\" 2>&1"
```

### PowerShell command
```bash
ssh -i ~/.ssh/shell_key -t -o StrictHostKeyChecking=no adora@100.116.86.38 "powershell -Command \"<command>\"" 2>&1
```

### Read large file (head)
```bash
ssh -i ~/.ssh/shell_key -t -o StrictHostKeyChecking=no adora@100.116.86.38 "powershell -Command \"Get-Content 'C:\\path\\to\\file' -Head 50\"" 2>&1
```

## RimWorld Save Files

RimWorld saves are at:
```
C:\Users\Adora\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Saves\
```

Save files (.rws) are **plain XML** (not compressed). Read with:
```bash
ssh -i ~/.ssh/shell_key -t -o StrictHostKeyChecking=no adora@100.116.86.38 "powershell -Command \"[System.IO.File]::ReadAllText('C:\\Users\\Adora\\AppData\\LocalLow\\Ludeon Studios\\RimWorld by Ludeon Studios\\Saves\\Autosave-3.rws')\"" 2>&1
```

Key XML elements in saves:
- `<meta><gameVersion>` — game version
- `<meta><modIds>` — loaded mods/DLC
- `<storyteller><def>` — Cassandra/Randy/Phoebe
- `<difficulty>` — Easy/Normal/Hard/etc.
- `<ticksGame>` — game age (÷60000 = days)
- `<pawns>` — colonist list (nick, gender, health)
- Colony name is in the save filename or `<name>` element

## Pitfalls

- **Windows path escaping in SSH**: Use double backslashes (`\\`) in PowerShell commands. Single backslashes may be interpreted as escape characters.
- **Apostrophes in filenames break PowerShell string literals**: A filename like `Her Majesty's Cult.rws` breaks single-quoted PowerShell strings. Use `Get-ChildItem -Filter 'Her Majesty*.rws'` to find the file by wildcard, then read via the returned `.FullName` property. Never embed apostrophes directly in a quoted path.
- **Output truncation**: Large files will be truncated. Use `Get-Content -Head N` or PowerShell substring extraction.
- **Player.log location**: `C:\Users\Adora\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Player.log`
- **RimWorld process name**: `RimWorldWin64.exe`
- **SSH key permissions**: The shell_key must have 600 permissions. If permission denied, check `chmod 600 ~/.ssh/shell_key`.
