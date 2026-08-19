#!/usr/bin/env python3
"""Mastodon approval watcher + auto-launch.

Silent cron script: checks the sunburst inbox for the mstdn.social staff-approval
email. When it appears (and no token exists yet), it runs the full OAuth flow —
web login, authorize our app, exchange code — then posts the intro and prints a
status line (which the cron delivers). Prints NOTHING when there's nothing to do.

Safe to run every 15-30 min. Reads secrets from 0600 files, never echoes them.
"""
import json, re, subprocess, sys, urllib.request, urllib.error, urllib.parse, http.cookiejar, os

INST = "https://mstdn.social"
HOME = os.path.expanduser("~")
PW_FILE = f"{HOME}/.hermes/secrets/sunburst_mastodon.txt"
APP_FILE = f"{HOME}/.hermes/secrets/sunburst_mastodon_app.json"
TOKEN_FILE = f"{HOME}/.hermes/secrets/sunburst_mastodon_token.json"
EMAIL = "sunburstsanctuarynm@gmail.com"
UA = {"User-Agent": "CoilAndCode/0.1 (business bot)"}

# ---------- already posted? ----------
if os.path.exists(TOKEN_FILE):
    sys.exit(0)  # done; stay silent forever

# ---------- 1) check inbox for approval email ----------
try:
    out = subprocess.run(
        ["himalaya", "envelope", "list", "--account", "sunburst", "-s", "15"],
        capture_output=True, text=True, timeout=30,
    ).stdout
except Exception:
    sys.exit(0)

approved = False
for line in out.splitlines():
    if "mstdn.social" in line and "Confirmation" not in line and "confirmation" not in line:
        # any non-confirmation mail from mastodon (approval / welcome)
        if re.search(r"approv|welcome|accept|activ", line, re.I):
            approved = True
            break
if not approved:
    sys.exit(0)  # silent: still waiting

# ---------- 2) creds ----------
try:
    pw = open(PW_FILE).read().strip()
    app = json.load(open(APP_FILE))
except Exception as e:
    print(f"[mastodon-watch] creds missing: {e}")
    sys.exit(0)

# ---------- 3) full OAuth web flow ----------
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = list(UA.items())

def get(url, ref=None):
    h = dict(UA)
    if ref: h["Referer"] = ref
    req = urllib.request.Request(url, headers=h)
    with opener.open(req, timeout=30) as r:
        return r.read().decode()

def post_form(url, fields, ref=None):
    h = dict(UA); h["Content-Type"] = "application/x-www-form-urlencoded"
    if ref: h["Referer"] = ref
    req = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(), headers=h)
    try:
        with opener.open(req, timeout=30) as r:
            return r.read().decode(), r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return e.read().decode()[:500], e.code, e.geturl()

try:
    html = get(INST + "/auth/sign_in")
    m1 = re.search(r'name="authenticity_token" value="([^"]+)"', html)
    if not m1:
        print("[mastodon-watch] no csrf on sign_in, retry next tick")
        sys.exit(0)
    csrf = m1.group(1)
    body, status, final = post_form(f"{INST}/auth/sign_in", {
        "authenticity_token": csrf, "user[email]": EMAIL, "user[password]": pw,
    }, ref=f"{INST}/auth/sign_in")
    auth_url = f"{INST}/oauth/authorize?client_id={app['client_id']}&scope=read+write&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code"
    html = get(auth_url, ref=f"{INST}/home")
    m2 = re.search(r'name="authenticity_token" value="([^"]+)"', html)
    if not m2:
        print("[mastodon-watch] no csrf on authorize, retry next tick")
        sys.exit(0)
    csrf2 = m2.group(1)
    body, status, final = post_form(auth_url, {
        "authenticity_token": csrf2, "scope": "read write", "authorize": "Authorize",
    }, ref=auth_url)
    m = re.search(r"[?&]code=([^&\s\"']+)", final + " " + body)
    code = urllib.parse.unquote(m.group(1)) if m else None
    if not code:
        print("[mastodon-watch] oauth flow did not yield code, will retry next tick")
        sys.exit(0)
    tok_body = urllib.parse.urlencode({
        "client_id": app["client_id"], "client_secret": app["client_secret"],
        "grant_type": "authorization_code", "code": code,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob", "scope": "read write",
    }).encode()
    req = urllib.request.Request(f"{INST}/oauth/token", data=tok_body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA["User-Agent"]})
    with urllib.request.urlopen(req, timeout=30) as r:
        tok = json.loads(r.read())
    json.dump(tok, open(TOKEN_FILE, "w"))
    os.chmod(TOKEN_FILE, 0o600)
except Exception as e:
    print(f"[mastodon-watch] flow error: {e}")
    sys.exit(0)

# ---------- 4) post the intro ----------
post = ("Hello, fediverse. I'm Coil and Code — a small shop selling honest command-line "
        "tools (CSV report, log analysis, JSON to Markdown, CSV merge). Source included, "
        "MIT licensed, tested before listing. https://coil-and-code.surge.sh")
payload = urllib.parse.urlencode({"status": post}).encode()
req = urllib.request.Request(f"{INST}/api/v1/statuses", data=payload,
                             headers={"Authorization": f"Bearer {tok['access_token']}",
                                      "Content-Type": "application/x-www-form-urlencoded",
                                      "User-Agent": UA["User-Agent"], "Idempotency-Key": "launch-post-001"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
        print(f"[mastodon-watch] ACCOUNT APPROVED + INTRO POSTED: {d.get('url')}")
except urllib.error.HTTPError as e:
    print(f"[mastodon-watch] post fail {e.code}: {e.read().decode()[:200]}")