# Himalaya v2.1.0 — Working Config & Send Recipe (Gmail)

The bundled `himalaya` skill documents the **v1 config format** (`backend.type`,
`message.send.backend.*`, `template` subcommand). As of himalaya v2.x (installed
`v2.1.0 +pimdir +imap +rustls-ring`, 2026-08-16), that format is obsolete and the
`template` subcommand is gone. This is the verified-working v2 setup. If a future
version changes the format again, regenerate the sample: `himalaya manual <dir>` produces
man pages from the installed binary — always trust the local `manual`/`--help` over the
bundled skill docs.

## Install
```bash
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh
# adds ~/.local/bin/himalaya
```

## Config — `~/.config/himalaya/config.toml` (v2 format)

```toml
[accounts.sunburst]
default = true

# IMAP
imap.server = "imaps://imap.gmail.com:993"
imap.sasl.plain.username = "you@gmail.com"
# read secret from a file line; NEVER embed the password in config
imap.sasl.plain.password.command = "tail -1 /home/youruser/.hermes/secrets/email.txt"

# SMTP (implicit TLS on 465)
smtp.server = "smtps://smtp.gmail.com:465"
smtp.sasl.plain.username = "you@gmail.com"
smtp.sasl.plain.password.command = "tail -1 /home/youruser/.hermes/secrets/email.txt"

# Gmail mailbox aliases — REQUIRED or save-to-Sent fails after delivery
mailbox.alias.inbox = "INBOX"
mailbox.alias.sent = "[Gmail]/Sent Mail"
mailbox.alias.drafts = "[Gmail]/Drafts"
mailbox.alias.trash = "[Gmail]/Trash"
```

Key format differences from the v1 skill docs:
- No `backend.type = "imap"` — use `imap.server = "imaps://host:port"` directly.
- Auth is `imap.sasl.plain.username` + `imap.sasl.plain.password.{raw|command}`.
- Folder aliases are `mailbox.alias.*` (not `folder.aliases.*`/`backend`).
- SMTP is `smtp.server` + `smtp.sasl.plain.*` (implicit `smtps://` on 465; `smtp://` + 
  `smtp.starttls` for 587).

## Verify
```bash
himalaya account list        # shows account + default flag
himalaya account check       # imap: OK / smtp: OK
himalaya mailbox list --counts
himalaya envelope list
```

## Send — v2 drops the `template` subcommand

`himalaya template send` (v1) is gone. Use `message compose` with the built-in flag
composer, `--send` to push over SMTP, `--save "sent"` to store a copy in Gmail's Sent:

```bash
himalaya message compose \
  --from "you@gmail.com" \
  --to "recipient@example.com" \
  --subject "Hello" \
  --body "$(cat << 'EOF'
Body text here.
EOF
)" \
  --send --save "sent"
```
Expect `Message successfully saved and sent`. If you only save without `--send`, use
`message compose ... --save "inbox"` etc.

## Gmail specifics
- **Regular account password is rejected for IMAP/SMTP.** You MUST generate an **App
  Password** (Google Account → Security → 2-Step Verification ON → App passwords), name it
  e.g. "Sunburst Daemon". The 16-char app password goes in the secrets file, not the
  regular login password.
- `himalaya account check` showing `IMAP AUTHENTICATE PLAIN failed` + `SMTP AUTH PLAIN
  failed` after switching to the app password confirms the config reached the server
  correctly and the credentials were the only issue.
- First sign-in from a new device/location triggers a handful of "Security alert" /
  "2-Step Verification turned on" emails to the inbox — normal, not a compromise.

## Secrets hygiene
- Keep the credential in `~/.hermes/secrets/<name>.txt` (chmod 600), one value per line,
  and reference it via `password.command` (e.g. `tail -1 <path>`). Never paste the
  password into config.toml — it's plaintext-readable.
- Gmail App Passwords don't show the chars again after creation — save immediately.
