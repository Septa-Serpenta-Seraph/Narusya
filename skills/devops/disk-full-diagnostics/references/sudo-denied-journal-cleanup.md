# Journal Cleanup When sudo Is Denied

## Problem
`journalctl --vacuum-time=3d` and `journalctl --vacuum-size=100M` fail with "Permission denied" when run as non-root, even when the journal is 800M+. The user account may not have sudo access or no password is available (cron context).

## What happens
```
journalctl --vacuum-time=3d
# Output: "Vacuuming done, freed 0B"
# Then: "Failed to delete archived journal ... Permission denied"
```

The vacuum command reports success but actually frees nothing because it can't delete the archived journal files owned by `systemd-journal` group.

## Workarounds (non-sudo)
None that actually free space. The journal files in `/var/log/journal/` are owned by root:systemd-journal with 0640 permissions.

## What to do instead
1. Report journal size as a **requires-sudo** item in cleanup reports
2. Flag it for the user to run manually: `sudo journalctl --vacuum-size=100M`
3. Suggest permanent fix in `/etc/systemd/journald.conf`:
   ```
   SystemMaxUse=200M
   MaxFileSec=7day
   ```
   Then `sudo systemctl restart systemd-journald`

## Lesson
Don't waste time retrying journal cleanup without sudo. Report it and move on to targets the agent can actually clean.
