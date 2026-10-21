---
name: windows-remote-gui-control
description: Remote Windows GUI control from a Linux VM over SSH.
version: 1.0.0
author: Narusya + Adora
license: MIT
metadata:
  hermes:
    tags: [windows, remote-control, gui, mouse, keyboard, screenshot, ssh, pyautogui]
---

# Remote Windows GUI Control

## When to Use

- User asks to play a game, click something, or interact with their Windows desktop
- User wants Narusya to move their mouse, type, or take screenshots on their PC
- Any task requiring GUI interaction on the Windows host (shell) from the VM
- Browser automation isn't sufficient — need desktop-level control

Control a Windows PC's mouse, keyboard, and screen from a Linux VM over SSH + Tailscale. The key insight: SSH sessions on Windows run in a non-interactive session (session 0), so direct `pyautogui` calls report screen size but can't actually grab the screen or move the real mouse. The fix is a listener script running in the **interactive session** via a scheduled task.

## Architecture

```
Linux VM (narusya)  ──SSH/SCP──►  Windows PC (shell)
  send command file                 naru_listener.py (interactive session)
  read result file                  pyautogui executes command
  OCR screenshot                    writes result + screenshot
```

## Prerequisites

1. **SSH access** to the Windows PC as the user (not admin). Use the hydra SSH key or password.
2. **Python 3.x** on Windows with `pyautogui` installed:
   `C:\Python313\python.exe -m pip install pyautogui`
3. **Scheduled task** running the listener in the interactive session (see Setup).

## Setup (one-time)

### 1. Deploy the listener script

Create `naru_listener.py` on the Windows PC. It watches `C:\Users\<user>\naru_cmd.txt`, executes commands with pyautogui, writes results to `naru_result.txt`.

SCP it:
```
scp -i ~/.hydra/hydra_ed25519 naru_listener.py adora@<ip>:C:/Users/Adora/naru_listener.py
```

### 2. Create the scheduled task (interactive)

```
schtasks /create /tn NaruListener /tr "C:\Python313\python.exe C:\Users\Adora\naru_listener.py" /sc onlogon /it /f
schtasks /run /tn NaruListener
```

The `/it` flag is critical — it runs in the interactive session where GUI access works.

### 3. Verify

```
printf "ping\n" > /tmp/naru_cmd.txt
scp ... /tmp/naru_cmd.txt adora@<ip>:C:/Users/Adora/naru_cmd.txt
ssh ... "type C:\Users\Adora\naru_result.txt"
# Should print: pong
```

## Command Protocol

Write one or more commands to `naru_cmd.txt` (one per line). Multiple commands in one file are executed sequentially — this is the efficient way to send a sequence (e.g., a drawing stroke). The listener deletes the file after processing and writes results to `naru_result.txt`. Poll for the result file (1-2s delay).

| Command | Args | Description |
|---|---|---|
| `move x y [dur]` | coords, optional duration | Move mouse |
| `click [x y] [btn]` | coords optional, button optional | Click |
| `doubleclick [x y]` | coords optional | Double-click |
| `rightclick [x y]` | coords optional | Right-click |
| `mousedown [btn]` | button optional (default left) | Press and hold mouse button |
| `mouseup [btn]` | button optional (default left) | Release mouse button |
| `dragto x y [dur]` | coords, optional duration | Drag to position (button held) |
| `drag x1 y1 x2 y2` | start and end coords | Drag from start to end |
| `type text` | free text | Type text |
| `key name` | key name | Press a key |
| `hotkey k1 k2 ...` | key names | Key combination |
| `scroll amount` | integer | Scroll (positive=up) |
| `pos` | — | Current mouse position |
| `size` | — | Screen dimensions |
| `screenshot` | — | Save to naru_screen.png |
| `sleep seconds` | float | Wait |
| `ping` | — | Heartbeat |
| `windows` | — | List all window titles |
| `focus title` | window title substring | Activate a window by title |
| `winpos title` | window title substring | Window position and size |
| `clipboard` | — | Read clipboard contents |
| `copyall` | — | Ctrl+A, Ctrl+C, read clipboard (grab text from focused app) |

## Reading the Screen

Since many models are text-only, use OCR:

```
# Take screenshot via listener
printf "screenshot\n" > naru_cmd.txt; scp ...; sleep 3
# Transfer back
scp adora@<ip>:C:/Users/Adora/naru_screen.png /tmp/naru_screen.png
# OCR
tesseract /tmp/naru_screen.png /tmp/naru_screen_text && cat /tmp/naru_screen_text.txt
```

## Pitfalls

- **SSH sessions can't access the interactive desktop.** Direct `pyautogui` via SSH reports screen size but `screenshot()` fails with "screen grab failed" and `position()` returns (0,0). You MUST run the listener in the interactive session via scheduled task with `/it`.
- **pyautogui FAILSAFE.** The default failsafe triggers when the mouse hits a screen corner. Set `pyautogui.FAILSAFE = False` in the listener, or the mouse will get stuck.
- **Command file is consumed.** The listener deletes `naru_cmd.txt` after processing. Write a new file each time. Poll for `naru_result.txt` (1-2s).
- **Screen resolution.** The interactive session reports the real resolution (e.g., 2560×1440), not the SSH session's virtual resolution.
- **Listener must be running.** If it's not running (task didn't start, crash), commands will pile up in the cmd file. Check with `schtasks /query /tn NaruListener`.
- **Kill the listener.** `schtasks /delete /tn NaruListener /f` removes the task. Also kill any running python process if needed.
- **No vision model available.** Use tesseract OCR on screenshots. For fast-paced games, this is too slow — works best for turn-based, strategy, puzzle, or slow games.
- **Game input.** Some games (especially DirectX/anti-cheat) may not respond to synthetic input. Test with a simple app first.

## Drawing in Apps (e.g., MS Paint)

- **Foreground is critical.** The target app must be the foreground window. Use `hotkey win d` (show desktop) then `focus <app>` before drawing. If another window (listener console, notepad) is on top, clicks hit the wrong window. This was the #1 cause of "drawing didn't register" during testing — not multi-segment vs single-segment.
- **Paint save dialog.** Ctrl+N in Paint triggers "Do you want to save?" — handle with `key d` (Don't save) or close and reopen Paint.
- **Multi-segment strokes:** chaining multiple `move` commands while the button is held (via `mousedown`...`mouseup`) may not register all intermediate points in some apps. If a single long `move` works but a multi-segment path doesn't, try: (a) fewer, longer segments with 0.3s+ duration each, (b) `dragto` instead of separate `move` commands, or (c) separate mousedown/move/mouseup per segment.
- **Verify drawings via pixel count.** Crop the canvas region from a screenshot and count dark pixels before/after. OCR can't detect drawings. Track the baseline dark-pixel count for the canvas so you can detect regressions.

## Navigating Web Apps via OCR

When controlling a browser on the Windows PC, use OCR to find clickable elements by text, then click at their coordinates:

1. **Take a screenshot** and run `tesseract <img> <out> tsv` to get word-level bounding boxes.
2. **Find the target text** in the TSV output — columns 7-10 give `left, top, width, height`.
3. **Click at center**: `left + width/2, top + height/2`.
4. **Verify** by taking another screenshot and OCR'ing.

```bash
# Example: find "File, View, or Amend All Returns" and click it
tesseract /tmp/screen.png /tmp/screen_tsv --psm 6 tsv
grep -i "returns" /tmp/screen_tsv.tsv
# left=1541 top=750 width=59 height=23 → click at (1570, 761)
```

This works for any web app where you can't use browser automation directly — tax portals, admin panels, legacy apps, etc. The TSV output gives precise click targets without visual inspection.

## Related Skills

- `hydra-protocol` — SSH access to Windows, key deployment, Tailscale IPs
- `narusya-vm-host-file-transfer` — file transfer between VM and Windows host
