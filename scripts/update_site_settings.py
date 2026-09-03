#!/usr/bin/env python3
"""Update WordPress site settings (title/tagline) via the REST API."""
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
    parser.add_argument("--title", help="site title")
    parser.add_argument("--tagline", help="site tagline (description)")
    args = parser.parse_args()

    payload = {}
    if args.title:
        payload["title"] = args.title
    if args.tagline:
        payload["description"] = args.tagline
    if not payload:
        sys.exit("nothing to update -- pass --title and/or --tagline")

    site, auth = wp_env()
    resp = requests.post(f"{site}/wp-json/wp/v2/settings", auth=auth, json=payload, timeout=30)
    resp.raise_for_status()
    updated = resp.json()
    print(f"title={updated['title']!r} tagline={updated['description']!r}")


if __name__ == "__main__":
    main()
