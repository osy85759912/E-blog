#!/usr/bin/env python3
"""Debug helper: list block templates and flag which ones mention '블로그'."""
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
    resp = requests.get(f"{site}/wp-json/wp/v2/templates", auth=auth, timeout=30)
    resp.raise_for_status()
    for t in resp.json():
        content = t.get("content", {}).get("raw", "")
        hit = "블로그" in content
        print(f"id={t['id']!r} slug={t['slug']!r} title={t['title']['rendered']!r} contains_블로그={hit}")
        if hit:
            # print the surrounding block markup for context
            idx = content.find("블로그")
            print("  context:", content[max(0, idx - 200) : idx + 200].replace("\n", " "))


if __name__ == "__main__":
    main()
