#!/usr/bin/env python3
"""Debug helper: check the current WordPress site title/tagline without ever
printing the raw value (a prior version printed it -- and even a base64
encoding of it -- but GitHub Actions masks any log text matching a secret's
value AND its base64 form, and this site's old title happens to equal one
of our secrets, so both attempts came back as '***'). Print lengths and a
boolean comparison instead."""
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
    parser.add_argument("--expect-title", help="print whether the live title equals this, instead of the raw value")
    args = parser.parse_args()

    site, auth = wp_env()
    resp = requests.get(f"{site}/wp-json/wp/v2/settings", auth=auth, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print("title_length:", len(data["title"]))
    print("tagline_length:", len(data["description"]))
    if args.expect_title:
        print("title_matches_expected:", data["title"] == args.expect_title)


if __name__ == "__main__":
    main()
