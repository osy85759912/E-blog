#!/usr/bin/env python3
"""One-off: check whether the live site is actually indexable by Google --
robots.txt, the homepage's <meta name="robots"> tag, and whether WordPress's
built-in XML sitemap is being served (WP core suppresses it automatically
when "discourage search engines" is turned on in Settings > Reading)."""
import os
import re
import sys

import requests


def main():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    if not site:
        sys.exit("missing WP_SITE_URL env var")

    resp = requests.get(f"{site}/robots.txt", timeout=30)
    print(f"robots.txt status: {resp.status_code}")
    print(resp.text if resp.ok else "(no robots.txt)")

    resp = requests.get(site, timeout=30)
    print(f"\nhomepage status: {resp.status_code}")
    match = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*>', resp.text, re.IGNORECASE)
    print(f"robots meta tag: {match.group(0) if match else '(none found)'}")

    resp = requests.get(f"{site}/wp-sitemap.xml", timeout=30)
    print(f"\nwp-sitemap.xml status: {resp.status_code}")
    if resp.ok:
        print(resp.text[:500])


if __name__ == "__main__":
    main()
