#!/usr/bin/env python3
"""One-off: add a responsive inline style to any <img> tag in a post's
content that doesn't already have one, so images fit mobile screens."""
import argparse
import re
import os
import sys

import requests

IMG_STYLE = "max-width:100%;height:auto;display:block;margin:16px auto;"


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def add_style(match):
    tag = match.group(0)
    if "style=" in tag:
        return tag
    return tag[:-2] + f' style="{IMG_STYLE}" />'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title-search", required=True)
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

    for post in posts:
        content = post["content"]["raw"]
        new_content = re.sub(r"<img [^>]*/>", add_style, content)
        if new_content == content:
            print(f"id={post['id']} no change needed")
            continue
        resp = requests.post(
            f"{site}/wp-json/wp/v2/posts/{post['id']}", auth=auth, json={"content": new_content}, timeout=30
        )
        resp.raise_for_status()
        print(f"id={post['id']} updated: {resp.json()['link']}")


if __name__ == "__main__":
    main()
