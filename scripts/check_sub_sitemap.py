#!/usr/bin/env python3
"""One-off: check the sub-sitemap that actually lists post URLs
(wp-sitemap-posts-post-1.xml), not just the top-level sitemap index --
Search Console's "couldn't fetch" could be on this file even if the
index itself is fine."""
import os
import sys

import requests


def main():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    if not site:
        sys.exit("missing WP_SITE_URL env var")

    for path in ("wp-sitemap-posts-post-1.xml", "wp-sitemap-posts-page-1.xml"):
        url = f"{site}/{path}"
        resp = requests.get(url, timeout=30)
        print(f"\n{path}: status={resp.status_code} content-type={resp.headers.get('content-type')}")
        print(resp.text[:600])


if __name__ == "__main__":
    main()
