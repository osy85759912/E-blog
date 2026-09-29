#!/usr/bin/env python3
"""Debug helper: dump the raw content of a specific block template by slug,
so we can see whether an archive/category page actually loops multiple
posts (list) or effectively renders like a single post."""
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
    parser.add_argument("--slug", required=True, help="template slug, e.g. archive, index, single")
    args = parser.parse_args()

    site, auth = wp_env()
    resp = requests.get(f"{site}/wp-json/wp/v2/templates", auth=auth, params={"context": "edit"}, timeout=30)
    resp.raise_for_status()
    for t in resp.json():
        if t["slug"] == args.slug:
            print(f"template id={t['id']} slug={t['slug']} source={t.get('source')}")
            print(t["content"]["raw"])
            return
    print(f"no template found with slug={args.slug}")


if __name__ == "__main__":
    main()
