#!/usr/bin/env python3
"""One-off: replace a WordPress page's content (used to rewrite the
About/Contact pages from stub-thin text into something substantive,
after an AdSense "low-value content" rejection)."""
import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-id", required=True, type=int)
    parser.add_argument("--content-file", required=True, help="HTML body")
    args = parser.parse_args()

    site, auth = wp_env()
    with open(args.content_file, encoding="utf-8") as f:
        content_html = f.read()

    resp = requests.post(
        f"{site}/wp-json/wp/v2/pages/{args.page_id}",
        auth=auth,
        json={"content": content_html},
        timeout=30,
    )
    resp.raise_for_status()
    page = resp.json()
    print(f"updated page id={page['id']} title={page['title']['raw']!r} -> {page['link']}")


if __name__ == "__main__":
    main()
