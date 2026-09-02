#!/usr/bin/env python3
import os
import sys

import requests

CATEGORY_TREE = {
    "일상": ["육아", "맛집", "여행"],
    "공부": ["주식"],
}


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def get_or_create_category(site, auth, name, parent=0):
    resp = requests.post(
        f"{site}/wp-json/wp/v2/categories",
        auth=auth,
        json={"name": name, "parent": parent},
        timeout=30,
    )
    if resp.status_code == 400 and resp.json().get("code") == "term_exists":
        return resp.json()["data"]["term_id"]
    resp.raise_for_status()
    return resp.json()["id"]


def main():
    site, auth = wp_env()
    for parent_name, children in CATEGORY_TREE.items():
        parent_id = get_or_create_category(site, auth, parent_name)
        print(f"{parent_name} -> id={parent_id}")
        for child_name in children:
            child_id = get_or_create_category(site, auth, child_name, parent=parent_id)
            print(f"  {child_name} -> id={child_id}")


if __name__ == "__main__":
    main()
