#!/usr/bin/env python3
"""One-off: check the things AdSense's "thin/low-value content" rejection
commonly hinges on -- required pages (About/Privacy/Contact) actually
having substantive text, and how many total posts/pages the site has."""
import os
import re
import sys

import requests


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def plain_len(html):
    return len(re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", html)))


def main():
    site, auth = wp_env()

    resp = requests.get(f"{site}/wp-json/wp/v2/pages", auth=auth, params={"context": "edit", "per_page": 50}, timeout=30)
    resp.raise_for_status()
    print("=== pages ===")
    for page in resp.json():
        content = page["content"]["raw"]
        print(f"id={page['id']} title={page['title']['raw']!r} plain_chars={plain_len(content)}")

    resp = requests.get(f"{site}/wp-json/wp/v2/posts", auth=auth, params={"status": "publish", "per_page": 1}, timeout=30)
    resp.raise_for_status()
    total_posts = resp.headers.get("X-WP-Total")
    print(f"\ntotal published posts: {total_posts}")

    resp = requests.get(f"{site}/wp-json/wp/v2/categories", auth=auth, params={"per_page": 50}, timeout=30)
    resp.raise_for_status()
    print("\n=== categories ===")
    for cat in resp.json():
        print(f"id={cat['id']} name={cat['name']!r} count={cat['count']}")


if __name__ == "__main__":
    main()
