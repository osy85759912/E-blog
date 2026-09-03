#!/usr/bin/env python3
"""One-off: split 공부>주식 into 공부>국내주식, 공부>미국주식.
Moves any posts currently in 주식 to 미국주식, then deletes 주식."""
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


def find_category(site, auth, name):
    resp = requests.get(
        f"{site}/wp-json/wp/v2/categories", auth=auth, params={"search": name, "per_page": 100}, timeout=30
    )
    resp.raise_for_status()
    for c in resp.json():
        if c["name"] == name:
            return c["id"]
    return None


def create_category(site, auth, name, parent=0):
    resp = requests.post(f"{site}/wp-json/wp/v2/categories", auth=auth, json={"name": name, "parent": parent}, timeout=30)
    if resp.status_code == 400 and resp.json().get("code") == "term_exists":
        return resp.json()["data"]["term_id"]
    resp.raise_for_status()
    return resp.json()["id"]


def main():
    site, auth = wp_env()

    study_id = find_category(site, auth, "공부")
    if not study_id:
        sys.exit("공부 category not found")

    domestic_id = create_category(site, auth, "국내주식", parent=study_id)
    us_id = create_category(site, auth, "미국주식", parent=study_id)
    print(f"국내주식 id={domestic_id}, 미국주식 id={us_id}")

    old_stock_id = find_category(site, auth, "주식")
    if old_stock_id:
        resp = requests.get(
            f"{site}/wp-json/wp/v2/posts",
            auth=auth,
            params={"categories": old_stock_id, "status": "any", "per_page": 100, "context": "edit"},
            timeout=30,
        )
        resp.raise_for_status()
        posts = resp.json()
        for post in posts:
            new_categories = [c for c in post["categories"] if c != old_stock_id]
            if us_id not in new_categories:
                new_categories.append(us_id)
            resp = requests.post(
                f"{site}/wp-json/wp/v2/posts/{post['id']}",
                auth=auth,
                json={"categories": new_categories},
                timeout=30,
            )
            resp.raise_for_status()
            print(f"moved post id={post['id']} title={post['title']['raw']!r} -> 미국주식")

        resp = requests.delete(f"{site}/wp-json/wp/v2/categories/{old_stock_id}", auth=auth, params={"force": True}, timeout=30)
        print(f"deleted 주식 category (id={old_stock_id}): {resp.status_code}")
    else:
        print("no existing 주식 category found (nothing to migrate)")


if __name__ == "__main__":
    main()
