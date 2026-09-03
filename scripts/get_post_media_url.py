#!/usr/bin/env python3
"""Debug helper: print the featured-image source_url for a post id."""
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
    parser.add_argument("--post-id", required=True, type=int)
    args = parser.parse_args()

    site, auth = wp_env()
    resp = requests.get(f"{site}/wp-json/wp/v2/posts/{args.post_id}", auth=auth, params={"context": "edit"}, timeout=30)
    resp.raise_for_status()
    post = resp.json()
    media_id = post.get("featured_media")
    if not media_id:
        sys.exit("post has no featured media")

    media_resp = requests.get(f"{site}/wp-json/wp/v2/media/{media_id}", auth=auth, timeout=30)
    media_resp.raise_for_status()
    print(media_resp.json()["source_url"])


if __name__ == "__main__":
    main()
