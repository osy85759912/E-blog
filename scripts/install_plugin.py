#!/usr/bin/env python3
"""Install (and optionally activate) a WordPress.org plugin via the REST API."""
import argparse
import json
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
    parser.add_argument("--slug", required=True, help="WordPress.org plugin slug, e.g. google-site-kit")
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()

    site, auth = wp_env()

    resp = requests.get(f"{site}/wp-json/wp/v2/plugins", auth=auth, params={"search": args.slug}, timeout=30)
    if resp.status_code != 200:
        sys.exit(f"cannot list plugins (status={resp.status_code}): {resp.text[:500]}")
    existing = [p for p in resp.json() if p["plugin"].startswith(f"{args.slug}/") or p["plugin"] == args.slug]

    if existing:
        plugin_file = existing[0]["plugin"]
        status = existing[0]["status"]
        print(f"already installed: {plugin_file} (status={status})")
    else:
        install_resp = requests.post(
            f"{site}/wp-json/wp/v2/plugins",
            auth=auth,
            json={"slug": args.slug},
            timeout=90,
        )
        if install_resp.status_code not in (200, 201):
            sys.exit(f"install failed (status={install_resp.status_code}): {install_resp.text[:1000]}")
        plugin_data = install_resp.json()
        plugin_file = plugin_data["plugin"]
        status = plugin_data["status"]
        print(f"installed: {plugin_file} (status={status})")

    if args.activate and status != "active":
        activate_resp = requests.post(
            f"{site}/wp-json/wp/v2/plugins/{plugin_file}",
            auth=auth,
            json={"status": "active"},
            timeout=30,
        )
        if activate_resp.status_code != 200:
            sys.exit(f"activate failed (status={activate_resp.status_code}): {activate_resp.text[:1000]}")
        print(f"activated: {plugin_file} (status={activate_resp.json()['status']})")


if __name__ == "__main__":
    main()
