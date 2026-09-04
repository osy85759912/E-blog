#!/usr/bin/env python3
"""One-off: check whether the Google Site Kit plugin is actually connected
(OAuth done, Search Console module active) via its own REST namespace.
Can't reach Google Search Console itself (no API access to the user's
Google account) -- this only confirms the WordPress-side plugin state."""
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

    resp = requests.get(f"{site}/wp-json/google-site-kit/v1/core/site/data/connection", auth=auth, timeout=30)
    print(f"connection status: {resp.status_code}")
    print(resp.text[:1000])

    resp = requests.get(f"{site}/wp-json/google-site-kit/v1/core/modules/data/list", auth=auth, timeout=30)
    print(f"\nmodules list status: {resp.status_code}")
    if resp.ok:
        for module in resp.json():
            if module.get("slug") in ("search-console", "analytics-4", "analytics"):
                print(f"  {module['slug']}: active={module.get('active')} connected={module.get('connected')}")
    else:
        print(resp.text[:500])


if __name__ == "__main__":
    main()
