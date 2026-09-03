#!/usr/bin/env python3
"""Activate or deactivate an already-installed WordPress plugin via the REST API."""
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
    parser.add_argument("--plugin", required=True, help="plugin file identifier, e.g. ninjafirewall/ninjafirewall")
    parser.add_argument("--status", required=True, choices=["active", "inactive"])
    args = parser.parse_args()

    site, auth = wp_env()
    resp = requests.post(
        f"{site}/wp-json/wp/v2/plugins/{args.plugin}",
        auth=auth,
        json={"status": args.status},
        timeout=30,
    )
    resp.raise_for_status()
    print(f"{args.plugin}: status={resp.json()['status']}")


if __name__ == "__main__":
    main()
