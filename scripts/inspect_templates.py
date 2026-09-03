#!/usr/bin/env python3
"""Debug helper: dump templates/template-parts and any wp_navigation
posts so we can see how (or whether) the header wires up a menu."""
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

    resp = requests.get(f"{site}/wp-json/wp/v2/templates", auth=auth, timeout=30)
    print(f"GET /templates -> {resp.status_code}")
    if resp.status_code == 200:
        for t in resp.json():
            has_nav = "wp:navigation" in (t.get("content", {}).get("raw") or "")
            print(f"  template slug={t['slug']} has_navigation_block={has_nav}")
            if has_nav:
                content = t["content"]["raw"]
                idx = content.find("wp:navigation")
                print("    snippet:", content[max(0, idx - 20): idx + 300])

    resp = requests.get(f"{site}/wp-json/wp/v2/template-parts", auth=auth, timeout=30)
    print(f"GET /template-parts -> {resp.status_code}")
    if resp.status_code == 200:
        for t in resp.json():
            has_nav = "wp:navigation" in (t.get("content", {}).get("raw") or "")
            print(f"  part slug={t['slug']} area={t.get('area')} has_navigation_block={has_nav}")
            if has_nav:
                content = t["content"]["raw"]
                idx = content.find("wp:navigation")
                print("    snippet:", content[max(0, idx - 20): idx + 300])

    resp = requests.get(f"{site}/wp-json/wp/v2/navigation", auth=auth, params={"status": "any"}, timeout=30)
    print(f"GET /navigation -> {resp.status_code}")
    if resp.status_code == 200:
        for n in resp.json():
            print(f"  navigation id={n['id']} title={n['title']['raw']!r} status={n['status']}")


if __name__ == "__main__":
    main()
