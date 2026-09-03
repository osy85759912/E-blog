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
    print(f"status_code: {resp.status_code}")
    try:
        updated = resp.json()
    except ValueError:
        print("response was not JSON, first 500 chars of body:")
        print(resp.text[:500])
        sys.exit(1)
    if "title" in payload:
        print(f"title_length: {len(updated.get('title', ''))}  matches_requested: {updated.get('title') == payload['title']}")
    if "description" in payload:
        print(
            f"tagline_length: {len(updated.get('description', ''))}  "
            f"matches_requested: {updated.get('description') == payload['description']}"
        )
    if resp.status_code >= 400:
        print("error response keys:", list(updated.keys()) if isinstance(updated, dict) else type(updated))
        sys.exit(1)


if __name__ == "__main__":
    main()
