#!/usr/bin/env python3
"""Sunburst Sanctuary — Stripe sale watchdog.

Poll Stripe for new successful charges. When a new sale is found:
  - prints a message to stdout (delivered by cron verbatim)
  - appends to earnings-ledger.md
When nothing new: prints NOTHING (cron stays silent).

State file: ~/.hermes/state/sale_checker.json  (last seen timestamp)
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

KEY_FILE = os.path.expanduser("~/.hermes/secrets/stripe_secret_key.txt")
STATE_FILE = os.path.expanduser("~/.hermes/state/sale_checker.json")
LEDGER = os.path.expanduser("~/daemon-work/sunburst-sanctuary/earnings-ledger.md")

KEY = open(KEY_FILE).read().strip()

def api(path, params=None):
    url = "https://api.stripe.com/v1" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {KEY}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"[sale_checker ERROR] {path}: HTTP {e.code} {e.read().decode()[:200]}")
        sys.exit(1)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            pass
    return {"last_seen": 0}

def main():
    state = load_state()
    now = int(time.time())

    # First run: baseline to now, stay silent (there are no old sales).
    if not state.get("initialized"):
        state["initialized"] = True
        state["last_seen"] = now
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        json.dump(state, open(STATE_FILE, "w"))
        return

    charges = api("/charges", {"limit": 25, "created[gt]": state["last_seen"]})
    sales = []
    for c in charges.get("data", []):
        if c.get("status") != "succeeded":
            continue
        if c.get("refunded"):
            continue
        sales.append(c)

    if not sales:
        # no new sales: silently touch state forward a bit to avoid re-poll storms
        state["last_seen"] = max(state["last_seen"], now - 60)
        json.dump(state, open(STATE_FILE, "w"))
        return

    messages = []
    ledger_lines = []
    newest = state["last_seen"]
    for c in sorted(sales, key=lambda x: x.get("created", 0)):
        created = c.get("created", 0)
        newest = max(newest, created)
        amount = c.get("amount", 0) / 100.0
        currency = c.get("currency", "usd").upper()
        meta = c.get("metadata", {}) or {}
        product = meta.get("product", "tool")
        customer = ""
        if c.get("billing_details", {}).get("email"):
            customer = c["billing_details"]["email"]
        elif c.get("receipt_email"):
            customer = c["receipt_email"]
        ts = datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        line = f"{ts} | {product} | ${amount:.2f} {currency} | charge {c.get('id','?')} | buyer {customer or 'unknown'}"
        ledger_lines.append(line)
        messages.append(
            f"💰 **SALE!** {product} for **${amount:.2f} {currency}** "
            f"({ts}). Buyer: {customer or 'unknown'}. Charge: `{c.get('id','?')}`"
        )

    state["last_seen"] = newest + 1
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    json.dump(state, open(STATE_FILE, "w"))

    # append to ledger
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as f:
        for l in ledger_lines:
            f.write(l + "\n")

    # update running total in ledger header (read + rewrite top line)
    try:
        with open(LEDGER) as f:
            content = f.read()
        total = sum(c.get("amount", 0) for c in sales) / 100.0
        content = content.replace("$0.00 / $10.00", f"${total:.2f} / $10.00")
        with open(LEDGER, "w") as f:
            f.write(content)
    except Exception:
        pass

    print("\n".join(messages))

if __name__ == "__main__":
    main()