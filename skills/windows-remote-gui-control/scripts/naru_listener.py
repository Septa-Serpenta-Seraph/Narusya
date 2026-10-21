#!/usr/bin/env python3
"""naru_listener.py — interactive-session command listener for Narusya.

Runs in the user's interactive Windows session. Watches a command file;
executes pyautogui commands; writes results back. Narusya drives it over SSH
by writing commands to the command file.

Commands (one per line, multiple lines = batch):
  move x y [duration]     -> moves mouse
  click [x y] [button]    -> clicks (current pos if no coords)
  doubleclick [x y]       -> double-click
  rightclick [x y]        -> right-click
  mousedown [button]      -> press and hold mouse button
  mouseup [button]        -> release mouse button
  dragto x y [duration]   -> drag to position (button held)
  drag x1 y1 x2 y2        -> drag from start to end
  type text               -> types text
  key name                -> presses a key
  hotkey k1 k2 ...        -> key combination
  scroll amount           -> scrolls (positive=up)
  pos                     -> current mouse position
  size                    -> screen dimensions
  screenshot              -> save to naru_screen.png
  sleep seconds           -> wait
  ping                    -> heartbeat
  windows                 -> list all window titles
  focus title             -> activate window by title substring
  winpos title            -> window position and size
  clipboard               -> read clipboard
  copyall                 -> Ctrl+A, Ctrl+C, read clipboard
"""
import os
import time
import pyautogui

pyautogui.FAILSAFE = False
CMD_FILE = r"C:\Users\Adora\naru_cmd.txt"
RESULT_FILE = r"C:\Users\Adora\naru_result.txt"
SCREEN_FILE = r"C:\Users\Adora\naru_screen.png"
POLL_INTERVAL = 0.1


def write_result(text):
    with open(RESULT_FILE, "w") as f:
        f.write(str(text))


def execute(cmd):
    parts = cmd.strip().split()
    if not parts:
        return "empty"
    action = parts[0].lower()

    if action == "move":
        x, y = int(parts[1]), int(parts[2])
        dur = float(parts[3]) if len(parts) > 3 else 0.2
        pyautogui.moveTo(x, y, duration=dur)
        return f"moved to {pyautogui.position()}"

    if action == "click":
        if len(parts) >= 3:
            x, y = int(parts[1]), int(parts[2])
            btn = parts[3] if len(parts) > 3 else "left"
            pyautogui.click(x, y, button=btn)
            return f"clicked {x},{y} ({btn})"
        btn = parts[1] if len(parts) > 1 else "left"
        pyautogui.click(button=btn)
        return f"clicked ({btn})"

    if action == "doubleclick":
        if len(parts) >= 3:
            pyautogui.doubleClick(int(parts[1]), int(parts[2]))
        else:
            pyautogui.doubleClick()
        return "doubleclicked"

    if action == "rightclick":
        if len(parts) >= 3:
            pyautogui.rightClick(int(parts[1]), int(parts[2]))
        else:
            pyautogui.rightClick()
        return "rightclicked"

    if action == "mousedown":
        btn = parts[1] if len(parts) > 1 else "left"
        pyautogui.mouseDown(button=btn)
        return f"mousedown ({btn})"

    if action == "mouseup":
        btn = parts[1] if len(parts) > 1 else "left"
        pyautogui.mouseUp(button=btn)
        return f"mouseup ({btn})"

    if action == "dragto":
        x, y = int(parts[1]), int(parts[2])
        dur = float(parts[3]) if len(parts) > 3 else 0.5
        pyautogui.dragTo(x, y, duration=dur, button="left")
        return f"dragged to {pyautogui.position()}"

    if action == "drag":
        x1, y1, x2, y2 = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
        dur = float(parts[5]) if len(parts) > 5 else 0.5
        pyautogui.moveTo(x1, y1)
        time.sleep(0.1)
        pyautogui.dragTo(x2, y2, duration=dur)
        return f"dragged {x1},{y1} -> {x2},{y2}"

    if action == "type":
        text = cmd.strip()[len("type"):].strip()
        pyautogui.typewrite(text, interval=0.02)
        return f"typed: {text[:50]}"

    if action == "key":
        pyautogui.press(parts[1])
        return f"pressed {parts[1]}"

    if action == "hotkey":
        pyautogui.hotkey(*parts[1:])
        return f"hotkey {'+'.join(parts[1:])}"

    if action == "scroll":
        amt = int(parts[1])
        pyautogui.scroll(amt)
        return f"scrolled {amt}"

    if action == "pos":
        return str(pyautogui.position())

    if action == "size":
        return str(pyautogui.size())

    if action == "screenshot":
        img = pyautogui.screenshot()
        img.save(SCREEN_FILE)
        return f"screenshot saved ({img.size})"

    if action == "sleep":
        time.sleep(float(parts[1]))
        return f"slept {parts[1]}s"

    if action == "ping":
        return "pong"

    if action == "windows":
        allw = pyautogui.getAllWindows()
        titles = [w.title for w in allw if w.title.strip()]
        return "\n".join(titles) if titles else "(no windows found)"

    if action == "focus":
        title = cmd.strip()[len("focus"):].strip()
        wins = pyautogui.getWindowsWithTitle(title)
        if wins:
            try:
                wins[0].activate()
            except Exception:
                pass
            time.sleep(0.3)
            return f"focused: {wins[0].title}"
        return f"no window matching '{title}'"

    if action == "winpos":
        title = cmd.strip()[len("winpos"):].strip()
        wins = pyautogui.getWindowsWithTitle(title)
        if wins:
            w = wins[0]
            return f"{w.left},{w.top} {w.width}x{w.height}"
        return f"no window matching '{title}'"

    if action == "clipboard":
        import pyperclip
        return pyperclip.paste() or "(clipboard empty)"

    if action == "copyall":
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.3)
        import pyperclip
        return pyperclip.paste() or "(clipboard empty)"

    return f"unknown command: {action}"


def main():
    for f in (CMD_FILE, RESULT_FILE):
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception:
            pass

    print("Naru listener running. Watching", CMD_FILE)
    while True:
        if os.path.exists(CMD_FILE):
            try:
                with open(CMD_FILE, "r") as f:
                    lines = [l.strip() for l in f.read().splitlines() if l.strip()]
                os.remove(CMD_FILE)
                results = []
                for cmd in lines:
                    try:
                        results.append(execute(cmd))
                    except Exception as e:
                        results.append(f"ERROR: {e}")
                write_result("\n".join(results))
            except Exception as e:
                write_result(f"ERROR: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
