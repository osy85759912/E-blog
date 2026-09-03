#!/usr/bin/env python3
"""Debug helper: print current WordPress site title/tagline."""
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
    resp = requests.get(f"{site}/wp-json/wp/v2/settings", auth=auth, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print("TITLE_B64:", __import__("base64").b64encode(data["title"].encode()).decode())
    print("TAGLINE_B64:", __import__("base64").b64encode(data["description"].encode()).decode())


if __name__ == "__main__":
    main()
