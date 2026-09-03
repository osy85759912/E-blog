#!/usr/bin/env python3
"""Debug helper: list all installed plugins and their status."""
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
    resp = requests.get(f"{site}/wp-json/wp/v2/plugins", auth=auth, params={"per_page": 100}, timeout=30)
    resp.raise_for_status()
    for p in resp.json():
        print(f"{p['plugin']}: status={p['status']} name={p['name']!r}")


if __name__ == "__main__":
    main()
