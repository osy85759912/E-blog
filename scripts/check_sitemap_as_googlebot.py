#!/usr/bin/env python3
"""One-off: Search Console shows "couldn't fetch" for wp-sitemap.xml.
Check whether the site's firewall (NinjaFirewall has blocked things
before) treats a Googlebot-style request differently from a plain
request -- status code, headers, and whether the body still looks like
valid sitemap XML."""
import os
import sys

import requests

GOOGLEBOT_UA = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)


def check(site, label, headers):
    resp = requests.get(f"{site}/wp-sitemap.xml", headers=headers, timeout=30)
    print(f"\n[{label}] status: {resp.status_code}")
    print(f"[{label}] content-type: {resp.headers.get('content-type')}")
    print(f"[{label}] first 300 chars:\n{resp.text[:300]}")
    return resp


def main():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    if not site:
        sys.exit("missing WP_SITE_URL env var")

    check(site, "plain requests (no UA override)", {})
    check(site, "Googlebot UA", {"User-Agent": GOOGLEBOT_UA})

    # also check robots.txt with the same two UAs, in case the firewall
    # serves a different robots.txt (or a challenge page) to bots
    for label, headers in (("plain", {}), ("Googlebot UA", {"User-Agent": GOOGLEBOT_UA})):
        resp = requests.get(f"{site}/robots.txt", headers=headers, timeout=30)
        print(f"\n[robots.txt / {label}] status: {resp.status_code}")
        print(resp.text[:300])


if __name__ == "__main__":
    main()
