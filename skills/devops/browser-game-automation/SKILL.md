---
name: browser-game-automation
description: Automate browser-based text adventures and web games. Use browser tools with keyboard shortcuts when type() fails.
category: devops
---

# Browser Game Automation

Use when playing text-based browser games (like Fenoxo TiTS, CoC2, etc.) via browser_navigate, browser_click, browser_press, and browser_vision.

## Key Pitfalls

### browser_type() 500 Errors
Many web games use custom input fields (not standard HTML input elements). browser_type will throw 500 Server Error on these.

**Workaround:**
1. First use browser_snapshot to find the correct element ref (look for textbox type elements).
2. If browser_type still fails, try keyboard approach:
   - Click into the text field: browser_click(ref)
   - Then use browser_press(key="Backspace") to clear existing text
   - Then try browser_type(ref, text) on the ref from snapshot, not vision

### Dialogue Advancement
Most Ren'Py/Ruffle-based text games (TiTS, CoC2) use keyboard shortcuts:
- N — advance dialogue / proceed to next screen
- Enter — confirm selection (does not always work via browser_press)
- Number keys (1-5, Q, W, etc.) — select options by their hotkey

**Tip:** If clicking visible buttons does not work, try the hotkey letter instead.

### TiTS Specific
- Next button behavior varies by screen — use browser_snapshot to find current screen ref
- The game sometimes auto-loads choices after pressing N
- Character creation uses hotkeys: 1, 2, 3, 4, 5, Q, W for different options
- **Greyed-out Next button:** After selecting an option, you may need to re-snapshot to see the Next button become active. Don't force-click it while disabled.
- **Hidden options require scrolling:** Some choice buttons are below the viewport. If snapshot shows narrative text but no choice buttons, browser_scroll(direction="down") then re-snapshot.
- **"Edit Bust" button (e16):** Present during creation screens but only functional at certain points. Ignore unless user specifically wants bust customization.
- **Update Notifications screen:** A dialog asking "Would you like the game to periodically check and notify if an update is available?" appears on every fresh load. Click "Yes" (spacebar) before proceeding to New Game.
- **No save between sessions:** TiTS does not persist character creation progress across browser session resets. If the tab goes stale (404 on snapshot/type/press), you must restart from New Game and redo character creation from scratch.
- **Full character creation flow:** Prologue (Mother species) → Mother confirmation → Name/Sex → Height → Thickness → Hair Pigment → Eye Pigment → Skin Pigment → Scale Pigment → Breast Size → Vaginal Traits → Sexual Gift → Affinity → (birth/game start follows)
- **No portraits during creation:** The left portrait box is empty/placeholder during character creation. Player character visual only appears after creation completes and the game proper begins.
- **Main menu ref IDs on fresh load:** After Update Notifications, "New Game" is typically ref e13 on the main menu screen.
- **Tab death mid-session:** TiTS tabs can 404 mid-session during character creation, not just between sessions. Symptoms: browser_snapshot, browser_type, browser_vision all return 404 after a click. This happens especially after the Sexual Gift/Affinity screen. Full reload required — browser_navigate → Update Notifications → New Game → redo creation from scratch.
- **No persistence even within a session:** If the tab dies during creation, nothing is saved. Every restart means going from Prologue to finish again. Don't expect any state to carry over.
- **Vision for portraits**: browser_vision is useful for checking if the character portrait has rendered yet. During creation, the left box is always empty or shows the doctor. The player character visual only appears after creation completes.

### Web Game Crashes
If the tab goes stale showing 404 on snapshot/type/press, use browser_navigate(url) to reload the game from scratch. You may need to restart character creation.

## Workflow Pattern
1. browser_navigate(url) — load the game
2. browser_snapshot() — get element tree (more reliable than vision for text games)
3. browser_click(ref) — click buttons
4. browser_vision — check visual state when text is cut off
5. browser_press(key="N") — advance dialogue
6. Repeat 2-5 for each screen
