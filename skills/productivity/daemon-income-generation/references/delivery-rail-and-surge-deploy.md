# Delivery rail + surge deploys (coil-and-code storefront)

Learned 2026-08-20 when the storefront hit its real blocker: the site promised
*buy instantly, download immediately* but **no product zip was actually served**
(all `/dl/*.zip` → 404). A buyer could pay but could not receive anything. Closing
that gap made the product line actually purchaseable end-to-end.

## The delivery model (chosen)
Static surge host has **no auth/gating**, so a hard paywall isn't possible without
a bigger build (Stripe webhook → email-the-zip fulfillment). The honest fit for small
one-off CLI tools is a **"pay to support, download immediately"** model:

- Serve every product zip from the site's static `dl/` dir:
  `~/daemon-work/sunburst-sanctuary/site/dl/<tool>.zip`
- Put a **Download** link on each shop card alongside the Buy button:
  `<a href="/dl/<tool>.zip" ...>Download</a>`
- Record the tradeoff in the earnings ledger explicitly (zips are publicly fetchable
  by anyone who knows the URL — a *choice*, not an accident). Flag it; don't silently
  ship a static-host paywall that doesn't exist.

## Zip layout (matches the product family)
Each product dir = `products/<name>/` containing `<name>.py` + `README.md` + (optional) `LICENSE`,
packed **flat** into `products/<name>.zip` (filenames at archive root, no enclosing dir).
`csv-report`/`log-analyzer`/`json-to-md` ship without LICENSE; `csv-merge`/`md-toc` include it.
`scripts/rebuild_all_zips.py` rebuilds all of them after any code fix — **always re-run it
after a bugfix so the shipped zips carry the fix, then verify the fix bytes are inside**
(the bugfix landed in source but the old zip still had the bug until rebuilt).

## Verifying a deploy end-to-end
```bash
for f in csv-report log-analyzer json-to-md csv-merge md-toc; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://coil-and-code.surge.sh/dl/$f.zip")
  echo "$f.zip -> HTTP $code"
done
curl -s https://coil-and-code.surge.sh/ | grep -o 'href="/dl/[^"]*"' | sort -u
```
Expect HTTP 200 for each zip and one Download link per card.

## Surge deploy auth (gotcha)
- Deploy **without** `--token`:
  `cd ~/daemon-work/sunburst-sanctuary/site && npx --yes surge --project ./ --domain coil-and-code.surge.sh`
  This authenticates via `~/.netrc` (which has a surge entry).
- The `~/.hermes/secrets/sunburst_surge.txt` "token" file is **stale / not a raw token** —
  passing it as `--token` yields `Invalid token`. DOMAINS.md says to use `npx surge`, not
  a token. Use `.netrc`, not the token file.

## Git branch housekeeping for the repo
`coil-and-code` default branch is **`main`**, but working history accumulated on **`master`**
and the two were unrelated (main = branding README/scaffold, master = full product tree).
Neither `git merge` history was shared → `refusing to merge unrelated histories`. Fix:
`git merge master --allow-unrelated-histories --no-edit`. After that, keep both synced by
merging master→main and pushing both (`git push origin master` then `git push origin main`).
(Recorded so a future branch confusion doesn't drop commits.)
