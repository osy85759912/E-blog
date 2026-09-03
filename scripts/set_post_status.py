#!/usr/bin/env python3
"""One-off: find a post by title substring and set its status (e.g. publish it live)."""
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
    parser.add_argument("--title-search", required=True)
    parser.add_argument("--status", required=True, choices=["publish", "draft", "pending", "future"])
    args = parser.parse_args()

    site, auth = wp_env()

    resp = requests.get(
        f"{site}/wp-json/wp/v2/posts",
        auth=auth,
        params={"search": args.title_search, "status": "any", "context": "edit", "per_page": 10},
        timeout=30,
    )
    resp.raise_for_status()
    posts = resp.json()
    if not posts:
        sys.exit(f"no post found matching {args.title_search!r}")
    post = posts[0]
    print(f"matched post id={post['id']} title={post['title']['raw']!r} current_status={post['status']}")

    resp = requests.post(
        f"{site}/wp-json/wp/v2/posts/{post['id']}",
        auth=auth,
        json={"status": args.status},
        timeout=30,
    )
    resp.raise_for_status()
    updated = resp.json()
    print(f"updated: {updated['link']} (status={updated['status']})")


if __name__ == "__main__":
    main()
