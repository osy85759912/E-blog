#!/usr/bin/env python3
"""Debug helper: list all pages plus which one (if any) is set as the posts page."""
import os
import sys

import requests


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def main():
    site, auth = wp_env()

    settings = requests.get(f"{site}/wp-json/wp/v2/settings", auth=auth, timeout=30)
    settings.raise_for_status()
    show_on_front = settings.json().get("show_on_front")
    page_for_posts = settings.json().get("page_for_posts")
    page_on_front = settings.json().get("page_on_front")
    print(f"show_on_front={show_on_front!r} page_for_posts={page_for_posts!r} page_on_front={page_on_front!r}")

    resp = requests.get(
        f"{site}/wp-json/wp/v2/pages", auth=auth, params={"per_page": 100, "context": "edit"}, timeout=30
    )
    resp.raise_for_status()
    for p in resp.json():
        print(f"id={p['id']} title={p['title']['raw']!r} slug={p['slug']!r} status={p['status']}")


if __name__ == "__main__":
    main()
