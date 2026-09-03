#!/usr/bin/env python3
"""One-off: fix a post that ended up with two "관련 종목 주가 차트" images
(update_post.py's replace-regex didn't match the original tag because it
carries a style="..." attribute, so it appended a second image instead of
replacing the first). Moves the newer image's URL into the original,
responsively-styled tag and removes the bare appended duplicate."""
import argparse
import os
import re
import sys

import requests

CHART_IMG = re.compile(r'<img[^>]*alt="관련 종목 주가 차트"[^>]*/>')


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-id", required=True, type=int)
    args = parser.parse_args()

    site, auth = wp_env()
    resp = requests.get(f"{site}/wp-json/wp/v2/posts/{args.post_id}", auth=auth, params={"context": "edit"}, timeout=30)
    resp.raise_for_status()
    content = resp.json()["content"]["raw"]

    matches = list(CHART_IMG.finditer(content))
    if len(matches) != 2:
        sys.exit(f"expected exactly 2 chart <img> tags, found {len(matches)} -- aborting without changes")

    old_tag, new_tag = matches[0].group(), matches[1].group()
    new_src_match = re.search(r'src="([^"]*)"', new_tag)
    if not new_src_match:
        sys.exit("could not find src on the second (newer) chart tag")
    new_src = new_src_match.group(1)

    fixed_old_tag = re.sub(r'src="[^"]*"', f'src="{new_src}"', old_tag, count=1)
    new_content = content.replace(old_tag, fixed_old_tag, 1).replace(new_tag, "", 1)

    update_resp = requests.post(
        f"{site}/wp-json/wp/v2/posts/{args.post_id}",
        auth=auth,
        json={"content": new_content},
        timeout=30,
    )
    update_resp.raise_for_status()

    verify = requests.get(
        f"{site}/wp-json/wp/v2/posts/{args.post_id}", auth=auth, params={"context": "edit"}, timeout=30
    )
    verify.raise_for_status()
    remaining = list(CHART_IMG.finditer(verify.json()["content"]["raw"]))
    print(f"chart <img> tags remaining: {len(remaining)}")
    if remaining:
        print("src ok:", new_src in remaining[0].group())


if __name__ == "__main__":
    main()
