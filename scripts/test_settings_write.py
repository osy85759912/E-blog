#!/usr/bin/env python3
"""Diagnostic: toggle an unrelated, harmless setting to see whether writes
to /wp/v2/settings persist at all, or whether the endpoint is broadly
neutered (as opposed to title/description specifically being blocked)."""
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

    before = requests.get(f"{site}/wp-json/wp/v2/settings", auth=auth, timeout=30)
    before.raise_for_status()
    current = before.json()["default_comment_status"]
    print(f"current default_comment_status: {current!r}")
    new_value = "closed" if current != "closed" else "open"

    post = requests.post(
        f"{site}/wp-json/wp/v2/settings",
        auth=auth,
        json={"default_comment_status": new_value},
        timeout=30,
    )
    print(f"POST status_code: {post.status_code}")
    post_body = post.json()
    print(f"POST response default_comment_status: {post_body.get('default_comment_status')!r}")

    after = requests.get(f"{site}/wp-json/wp/v2/settings", auth=auth, timeout=30)
    after.raise_for_status()
    print(f"GET after default_comment_status: {after.json()['default_comment_status']!r}")

    # restore original value regardless of outcome
    requests.post(
        f"{site}/wp-json/wp/v2/settings",
        auth=auth,
        json={"default_comment_status": current},
        timeout=30,
    )
    print(f"restored to: {current!r}")


if __name__ == "__main__":
    main()
