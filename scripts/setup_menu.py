#!/usr/bin/env python3
"""One-off setup: create a nav menu with the 일상>육아/맛집/여행,
공부>주식 category structure and assign it to a menu location, via the
WordPress REST API (core menu endpoints added in WP 5.9)."""
import os
import sys

import requests

STRUCTURE = {
    "일상": ["육아", "맛집", "여행"],
    "공부": ["주식"],
}
MENU_NAME = "메인 메뉴"


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


def find_or_create_menu(site, auth):
    resp = requests.get(f"{site}/wp-json/wp/v2/menus", auth=auth, params={"per_page": 100}, timeout=30)
    print(f"[menu] GET /menus -> {resp.status_code}", file=sys.stderr)
    resp.raise_for_status()
    for m in resp.json():
        if m["name"] == MENU_NAME:
            return m["id"]
    resp = requests.post(f"{site}/wp-json/wp/v2/menus", auth=auth, json={"name": MENU_NAME}, timeout=30)
    print(f"[menu] POST /menus -> {resp.status_code} {resp.text[:300]}", file=sys.stderr)
    resp.raise_for_status()
    return resp.json()["id"]


def add_menu_item(site, auth, menu_id, title, url, category_id, order, parent=0):
    payload = {
        "title": title,
        "url": url,
        "menus": menu_id,
        "menu_order": order,
        "parent": parent,
        "object": "category",
        "object_id": category_id,
        "type": "taxonomy",
        "status": "publish",
    }
    resp = requests.post(f"{site}/wp-json/wp/v2/menu-items", auth=auth, json=payload, timeout=30)
    print(f"[menu] POST /menu-items ({title}) -> {resp.status_code} {resp.text[:300]}", file=sys.stderr)
    resp.raise_for_status()
    return resp.json()["id"]


def assign_location(site, auth, menu_id):
    resp = requests.get(f"{site}/wp-json/wp/v2/menu-locations", auth=auth, timeout=30)
    print(f"[menu] GET /menu-locations -> {resp.status_code} {resp.text[:500]}", file=sys.stderr)
    resp.raise_for_status()
    locations = resp.json()
    if not locations:
        print("[menu] no menu locations registered by this theme", file=sys.stderr)
        return None
    location_name = next(iter(locations.keys()))
    resp = requests.post(
        f"{site}/wp-json/wp/v2/menu-locations/{location_name}",
        auth=auth,
        json={"menu": menu_id},
        timeout=30,
    )
    print(f"[menu] POST /menu-locations/{location_name} -> {resp.status_code} {resp.text[:300]}", file=sys.stderr)
    return location_name if resp.status_code < 300 else None


def main():
    site, auth = wp_env()
    menu_id = find_or_create_menu(site, auth)
    print(f"menu id={menu_id}")

    order = 1
    for parent_name, children in STRUCTURE.items():
        parent_id, parent_link = get_category(site, auth, parent_name)
        if not parent_id:
            print(f"category not found: {parent_name}")
            continue
        parent_item_id = add_menu_item(site, auth, menu_id, parent_name, parent_link, parent_id, order)
        order += 1
        for child_name in children:
            child_id, child_link = get_category(site, auth, child_name)
            if not child_id:
                continue
            add_menu_item(site, auth, menu_id, child_name, child_link, child_id, order, parent=parent_item_id)
            order += 1

    location = assign_location(site, auth, menu_id)
    if location:
        print(f"assigned menu to location: {location}")
    else:
        print("could not auto-assign a menu location -- may need manual assignment in wp-admin")


if __name__ == "__main__":
    main()
