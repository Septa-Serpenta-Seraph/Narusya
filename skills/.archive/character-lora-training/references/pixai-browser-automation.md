# Driving PixAI.art headlessly via Camoufox REST server

Verified 2026-08-25 (signup + login persistence + LoRA attach + prompt injection).
Server: camofox-browser on `http://localhost:9377` (see camoufox-browser-setup skill).

## API essentials

The old `/session` routes are gone. Current shape:

```
POST   /tabs                          {"userId","sessionKey","url"} -> {tabId}
POST   /tabs/:id/navigate             {"userId","sessionKey","url"}
GET    /tabs/:id/snapshot?userId=...&sessionKey=...   # a11y tree, refs e1..eN
POST   /tabs/:id/click                {"userId","ref"}  or  {"selector": "text=Foo"}
POST   /tabs/:id/type                 {"userId","ref","text"}   # ref-form only
POST   /tabs/:id/evaluate             {"userId","expression":"(() => {...})()"} -> {ok,result}
DELETE /tabs/:id?userId=...
```

- Refs reset on navigation — re-snapshot after every page change.
- Sessions expire after ~30 min idle; tabs vanish. Just open a new tab and log in again.
- `selector` clicks accept Playwright syntax incl. `text=Image Generation` (worked when
  a11y option elements had no refs). Selector click on `[role=option]` alone 500s.

## Login flow (email path)

1. Navigate to `https://pixai.art/en/login` (direct nav is more reliable than clicking
   "Sign in", which may not open the modal in headless).
2. Click `Continue with Email`, snapshot to get refs for Email/Password/Continue textboxes.
3. Type creds via ref-form `/type`, click Continue.
4. Logged-in detection: banner shows `Top up`/`Bonus Credits` buttons instead of `Sign in`.
5. Signup itself needs no email verification to become usable; verification mail (if any)
   arrives via the readable inbox — harvest confirm links with himalaya.

## The contenteditable prompt trap (important)

PixAI's prompt editor is a **contenteditable div**, not a textarea:
- ref-form `/type` returns 422 against it
- selector-form `/type` on `textarea` finds nothing
Fix — inject via `/evaluate`:

```js
(() => {
  const ce = document.querySelector('[contenteditable=true]');
  ce.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, PROMPT_JSON_HERE);
  return 'ok:' + ce.textContent.slice(0,40);
})()
```

(`execCommand('insertText')` fires the input events React needs; setting textContent
directly does NOT register with the framework.)

## LoRA attach flow

From a model page (`pixai.art/model/<id>`): click **Use this LoRA** → mode dialog
"Choose Generation Mode" appears → click `text=Image Generation` → generator opens with
the LoRA chip already attached (`checkbox "Narusya" [checked]` in the tree).

## Credits reality

- Balance shows as a numeric button in the banner; snapshot regex `button "([\d,]+)"`.
- SDXL generation ≈ 6,600 credits/image. With 0 balance, Generate pops a purchase dialog
  (dismiss and report honestly).
- Daily Reward "Receive" was persistently disabled and Check-in didn't increment on a
  fresh account — likely gated behind email verification that took hours. Don't hammer;
  re-check later or use an account with banked credits.

## Credentials hygiene

Store signup creds at `~/.hermes/secrets/pixai_account.txt` chmod 600 BEFORE submitting
any form. Never echo them into logs or chat.
