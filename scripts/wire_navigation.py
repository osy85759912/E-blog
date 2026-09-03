#!/usr/bin/env python3
"""One-off: replace the auto-generated page-list navigation with our
category structure (일상>육아/맛집/여행, 공부>주식), and stop forcing
the nav into an always-collapsed overlay/hamburger menu."""
import os
import sys

import requests

STRUCTURE = {
    "일상": ["육아", "맛집", "여행"],
    "공부": ["주식"],
}
NAV_ID = 4
HEADER_PART_ID = "twentytwentyfive//vertical-header"


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def get_category(site, auth, name):
    resp = requests.get(
        f"{site}/wp-json/wp/v2/categories", auth=auth, params={"search": name, "per_page": 100}, timeout=30
    )
    resp.raise_for_status()
    for c in resp.json():
        if c["name"] == name:
            return c["id"], c["link"]
    return None, None


def build_nav_content(site, auth):
    blocks = []
    for parent_name, children in STRUCTURE.items():
        parent_id, parent_link = get_category(site, auth, parent_name)
        if not parent_id:
            print(f"category not found: {parent_name}")
            continue
        child_blocks = []
        for child_name in children:
            child_id, child_link = get_category(site, auth, child_name)
            if not child_id:
                continue
            child_blocks.append(
                f'<!-- wp:navigation-link {{"label":"{child_name}","type":"category","id":{child_id},'
                f'"url":"{child_link}","kind":"taxonomy"}} /-->'
            )
        submenu = (
            f'<!-- wp:navigation-submenu {{"label":"{parent_name}","type":"category","id":{parent_id},'
            f'"url":"{parent_link}","kind":"taxonomy"}} -->\n'
            + "\n".join(child_blocks)
            + "\n<!-- /wp:navigation-submenu -->"
        )
        blocks.append(submenu)
    return "\n\n".join(blocks)


def main():
    site, auth = wp_env()

    content = build_nav_content(site, auth)
    print("new navigation content:\n", content)
    resp = requests.post(
        f"{site}/wp-json/wp/v2/navigation/{NAV_ID}",
        auth=auth,
        json={"content": content, "status": "publish"},
        timeout=30,
    )
    resp.raise_for_status()
    print(f"updated navigation id={NAV_ID}")

    part_url = f"{site}/wp-json/wp/v2/template-parts/{HEADER_PART_ID}"
    resp = requests.get(part_url, auth=auth, params={"context": "edit"}, timeout=30)
    resp.raise_for_status()
    part_content = resp.json()["content"]["raw"]

    if '"overlayMenu":"always"' in part_content:
        new_part_content = part_content.replace('"overlayMenu":"always"', '"overlayMenu":"mobile"')
        resp = requests.post(part_url, auth=auth, json={"content": new_part_content}, timeout=30)
        resp.raise_for_status()
        print("set overlayMenu to mobile (was: always)")
    else:
        print("overlayMenu:always not found -- no change made to header part")


if __name__ == "__main__":
    main()
