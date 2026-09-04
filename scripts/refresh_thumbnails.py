#!/usr/bin/env python3
"""One-off: regenerate the featured-image thumbnail (new labeled index +
stock stat design) for every already-published real post, and swap it into
both the post's featured_media and the inline cover <img> at the top of the
body, matched by title search."""
import argparse
import glob
import mimetypes
import os
import re
import subprocess
import sys

import requests

PUBLISHED_DIR = "published"
# only the real daily posts -- YYYY-MM-DD.md or kr-YYYY-MM-DD.md -- skip the
# various *-test.md scratch files used to preview the thumbnail design.
REAL_POST_RE = re.compile(r"^(kr-)?\d{4}-\d{2}-\d{2}\.md$")


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def upload_media(site, auth, image_path):
    mime, _ = mimetypes.guess_type(image_path)
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                "Content-Disposition": f'attachment; filename="{os.path.basename(image_path)}"',
                "Content-Type": mime or "application/octet-stream",
            },
            data=f.read(),
            timeout=90,
        )
    resp.raise_for_status()
    media = resp.json()
    return media["id"], media["source_url"]


def parse_frontmatter(text):
    if not text.startswith("---"):
        sys.exit("draft file missing --- frontmatter block")
    _, fm, _ = text.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def find_post(site, auth, title):
    resp = requests.get(
        f"{site}/wp-json/wp/v2/posts",
        auth=auth,
        params={"search": title, "status": "any", "context": "edit", "per_page": 10},
        timeout=30,
    )
    resp.raise_for_status()
    for post in resp.json():
        if post["title"]["raw"] == title:
            return post

    # the "search" param can come up empty for titles containing characters
    # like "-4%" (seen with the Snowflake post) even though the post exists
    # -- fall back to an unfiltered listing and match client-side.
    resp = requests.get(
        f"{site}/wp-json/wp/v2/posts",
        auth=auth,
        params={"status": "any", "context": "edit", "per_page": 100},
        timeout=30,
    )
    resp.raise_for_status()
    for post in resp.json():
        if post["title"]["raw"] == title:
            return post
    return None


def refresh_one(site, auth, path):
    with open(path, encoding="utf-8") as f:
        meta = parse_frontmatter(f.read())

    title = meta["title"]
    tickers = meta.get("tickers")
    if not tickers:
        print(f"skip {path}: no tickers, nothing to regenerate")
        return
    category = meta.get("category", "미국주식")
    person = meta.get("thumbnail_person")
    mood = meta.get("mood", "중립")
    market = "kr" if category == "국내주식" else "us"
    primary_ticker = tickers.split(",")[0].strip()

    post = find_post(site, auth, title)
    if post is None:
        print(f"skip {path}: no live post found matching title {title!r}")
        return

    base = os.path.splitext(os.path.basename(path))[0]
    thumb_path = f"/tmp/refresh-{base}-thumb.png"
    thumb_cmd = [
        sys.executable, "scripts/generate_thumbnail.py",
        "--ticker", primary_ticker, "--title", title, "--mood", mood,
        "--market", market, "--out", thumb_path,
    ]
    if person:
        thumb_cmd += ["--person", person]
    subprocess.run(thumb_cmd, check=True)

    thumb_id, thumb_url = upload_media(site, auth, thumb_path)

    content = post["content"]["raw"]
    cover_pattern = rf'<img[^>]*alt="{re.escape(title)}"[^>]*/>'

    def swap_src(match):
        return re.sub(r'src="[^"]*"', f'src="{thumb_url}"', match.group(), count=1)

    new_content, count = re.subn(cover_pattern, swap_src, content, count=1)
    if count == 0:
        img_style = "max-width:100%;height:auto;display:block;margin:16px auto;"
        new_content = f'<img src="{thumb_url}" alt="{title}" style="{img_style}" />\n' + content
        print(f"  no existing cover <img> found in body, prepended new one")

    resp = requests.post(
        f"{site}/wp-json/wp/v2/posts/{post['id']}",
        auth=auth,
        json={"content": new_content, "featured_media": thumb_id},
        timeout=30,
    )
    resp.raise_for_status()
    updated = resp.json()
    print(f"refreshed id={updated['id']} title={title!r} -> {updated['link']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only", help="comma-separated basenames (e.g. 2026-09-03.md) to limit the refresh to, default: all real posts"
    )
    args = parser.parse_args()

    site, auth = wp_env()
    files = sorted(
        p for p in glob.glob(f"{PUBLISHED_DIR}/*.md")
        if REAL_POST_RE.match(os.path.basename(p))
    )
    if args.only:
        wanted = {name.strip() for name in args.only.split(",") if name.strip()}
        files = [p for p in files if os.path.basename(p) in wanted]
    if not files:
        sys.exit("no matching published posts found")

    for path in files:
        refresh_one(site, auth, path)


if __name__ == "__main__":
    main()
