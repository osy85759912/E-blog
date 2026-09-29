#!/usr/bin/env python3
"""Fix: the home/archive templates' query-loop post-template used the
`core/post-content` block, which renders each post's FULL body inline --
so clicking a category menu item looked like landing straight on an
article instead of seeing a list of posts. Swap that block for
`core/post-excerpt` (title + short summary + "more" link) so archive and
category pages read as an actual list."""
import argparse
import sys
import os

import requests

OLD_BLOCK = '<!-- wp:post-content {"align":"full","fontSize":"medium","layout":{"type":"constrained"}} /-->'
NEW_BLOCK = '<!-- wp:post-excerpt {"align":"full","fontSize":"medium","excerptLength":40,"moreText":"더 보기 »"} /-->'


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-id", required=True, help='e.g. "twentytwentyfive//home"')
    args = parser.parse_args()

    site, auth = wp_env()

    resp = requests.get(f"{site}/wp-json/wp/v2/templates/{args.template_id}", auth=auth, timeout=30)
    resp.raise_for_status()
    content = resp.json()["content"]["raw"]

    count = content.count(OLD_BLOCK)
    if count != 1:
        sys.exit(f"expected exactly 1 occurrence of post-content block in {args.template_id!r}, found {count} -- aborting without changes")

    new_content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)

    update_resp = requests.post(
        f"{site}/wp-json/wp/v2/templates/{args.template_id}",
        auth=auth,
        json={"content": new_content},
        timeout=30,
    )
    update_resp.raise_for_status()

    verify = requests.get(f"{site}/wp-json/wp/v2/templates/{args.template_id}", auth=auth, timeout=30)
    verify.raise_for_status()
    ok = "wp:post-excerpt" in verify.json()["content"]["raw"]
    print(f"{args.template_id}: switched_to_excerpt={ok}")


if __name__ == "__main__":
    main()
