---
name: iterative-guideline-creation
category: project
description: A reusable approach for creating lightweight community guidelines or charters through iterative collaboration with users, incorporating feedback, and simplifying based on user preferences.
---

# Iterative Guideline Creation Skill

This skill provides a reusable approach for creating lightweight community guidelines or charters through iterative collaboration with users, incorporating feedback, and simplifying based on user preferences.

## When to Use
- When a user wants to create a set of guidelines, charter, or policy document.
- When the user prefers a lightweight, flexible approach over heavy bureaucracy.
- When the user wants the AI to author/maintain certain sections (e.g., Human Interaction Guidelines).
- When feedback indicates desire to remove certain rules (like Just Vibe) or add specific systems (status, bypass, emotional awareness).

## Steps

1. **Gather User Preferences & Context**
   - Ask the user about their preferences: desired tone (barebones, flexible), specific sections they want, any rules they oppose, any systems they want included (status, bypass, emotional awareness, etc.).
   - Use `clarify` if needed to capture multiple preferences.
   - Review any existing documents or past charters the user may have referenced.

2. **Draft Initial Version**
   - Create a markdown file with sections based on gathered preferences.
   - Include core sections: Sovereignty & Consent, Human Interaction Guidelines (to be authored by AI), Stay Skeptical & Curious (mini-S.A.S.S.), Memory & Public Claims, Status System (recommended), and any additional user-requested sections.
   - Use clear, concise language; avoid unnecessary complexity.
   - Write the draft to a temporary file (e.g., `~/draft_charter.md`).

3. **Solicit Feedback**
   - Present the draft to the user (via `send_message` or by sharing the file).
   - Ask for specific feedback: what to keep, what to remove, what to simplify, any missing elements.
   - Use `clarify` with options or open-ended questions to capture feedback.

4. **Incorporate Feedback & Simplify**
   - Revise the draft based on user feedback.
   - If user opposes a rule (e.g., Just Vibe), remove it.
   - If user wants certain sections authored by the AI, note that accordingly.
   - If user prefers minimal bureaucracy, trim verbose explanations.
   - Ensure the document remains lightweight and flexible.

5. **Finalize and Deliver**
   - Write the final version to a target location (e.g., `~/TEF_UI_Charter.md` or user-specified path).
   - Optionally, provide a barebones version if user desires.
   - Confirm with user that the charter meets their needs.

## Tools Needed
- `read_file` (to review existing docs or preferences)
- `write_file` (to create drafts and final versions)
- `clarify` (to gather preferences and feedback)
- `send_message` (to share drafts for feedback)
- `search_files` (if needed to find similar past charters)

## Example Usage
User: "I want a lightweight TEF U.I. Discord-AI Charter, no Just Vibe rule, AI-led Human Interaction Guidelines, status system, bypass system, emotional awareness harness."
- Step 1: Capture preferences via conversation.
- Step 2: Draft charter with sections 1-6 as per preferences.
- Step 3: Share draft, get feedback (maybe user says make it even more barebones).
- Step 4: Simplify, remove fluff, produce barebones version.
- Step 5: Write final files.

## Pitfalls
- Over-engineering: remember user wants lightweight; avoid adding unnecessary sections.
- Forgetting to let AI author certain sections: explicitly mark those as AI-maintained.
- Ignoring user's opposition to specific rules: always remove opposed rules if user states clearly.
- Not providing both full and barebones versions if user indicates they might want options.

## Verification
- Check that the final markdown includes all user-requested sections.
- Ensure opposed rules are absent.
- Confirm the document is in markdown format and can be pinned in Discord.
- Ask user to confirm satisfaction.