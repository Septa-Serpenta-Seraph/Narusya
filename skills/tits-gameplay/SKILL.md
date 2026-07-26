---
name: tits-gameplay
description: Browser gameplay strategy and automation for "Trials in Tainted Space" (TiTS) via browser tools.
category: gaming
---

# TiTS Browser Play Strategy

## Context
Playing "Trials in Tainted Space" via Hermes browser tools.
URL: `https://www.fenoxo.com/play/TiTS/release/`

## Resilience Patterns
1.  **Tab Crashes:** The browser tab frequently crashes/returns 404 during character creation (especially after selecting stats).
    *   **Symptom:** `browser_snapshot` returns `404 Client Error`.
    *   **Action:** Re-navigate immediately. **Note:** The game does NOT save creation progress. You must restart from the Prologue ("The Past").
2.  **State Sync:** The game UI updates asynchronously.
    *   **Symptom:** Snapshot shows options but they are missing or "Next" is grayed out.
    *   **Action:** Use `browser_vision` (question: "Are the next buttons active or grayed out?") to visually confirm state before clicking.

## Character Creation Spec (Scylla Build)
**Prologue:**
1.  Skip "The Past" (click Next).
2.  **Race:** Suula.
3.  **Confirmation:** Yes.

**Stats (Rapid Re-entry Path):**
*   **Name:** Scylla (textbox ref usually e18).
*   **Sex:** Female.
*   **Height:** Very Tall (5).
*   **Thickness:** Thickset (Q).
*   **Hair Pigment:** Red (2).
*   **Eye Pigment:** Red (3).
*   **Skin Pigment:** Ebony (W).
*   **Scale Pigment:** Gold (5).
*   **Breast Size:** Big GG (W).
*   **Vaginal Traits:** Capacity (1).
*   **Sexual Gift:** Extra Ardor (T).
*   **Affinity:** Willpower (5).
*   **Upbringing:** Austere (4).

## Tips
*   Commit the sequence to memory to minimize tool calls during re-runs.
*   Use `browser_vision` to capture the final portrait for the user ("Adora") once the game renders her after birth.
*   The "Update Notifications" pop-up appears on every load. Click "Yes" immediately (ref usually e29).
