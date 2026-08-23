#!/usr/bin/env python3
"""Create a Stripe product + price + payment link for a Coil-and-Code tool.

Usage: python3 create_stripe_listing.py "Tool Name" "One-line description" 1200
Price in cents (1200 = $12.00).
Prints: PRODUCT_ID  PRICE_ID  PAYMENT_LINK_URL
"""
import json
import os
import sys
import urllib.parse
import urllib.request

SECRET = os.path.expanduser("~/.hermes/secrets/stripe_secret_key.txt")


def api(path, params):
    with open(SECRET) as f:
        key = f.read().strip()
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        f"https://api.stripe.com/v1/{path}", data=data, method="POST",
        headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    name, desc = sys.argv[1], sys.argv[2]
    cents = int(sys.argv[3])
    prod = api("products", {"name": name, "description": desc})
    price = api("prices", {"product": prod["id"], "unit_amount": str(cents), "currency": "usd"})
    link = api("payment_links", {"line_items[0][price]": price["id"], "line_items[0][quantity]": "1"})
    print(f"{prod['id']}  {price['id']}  {link['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())