#!/usr/bin/env python3
"""One-off: regenerate the chart for a specific post (matched by title
search), swap it into the post content, and publish the post live."""
import argparse
import mimetypes
import os
import re
import subprocess
import sys

import requests


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
    return media["source_url"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title-search", required=True)
    parser.add_argument("--tickers", required=True)
    parser.add_argument("--publish", action="store_true", help="set status to publish (live)")
    args = parser.parse_args()

    site, auth = wp_env()

    resp = requests.get(
        f"{site}/wp-json/wp/v2/posts",
        auth=auth,
        params={"search": args.title_search, "status": "any", "context": "edit", "per_page": 10},
        timeout=30,
    )
    resp.raise_for_status()
    posts = resp.json()
    if not posts:
        sys.exit(f"no post found matching {args.title_search!r}")
    post = posts[0]
    print(f"matched post id={post['id']} title={post['title']['raw']!r}")

    chart_path = "/tmp/update-chart.png"
    subprocess.run(
        [sys.executable, "scripts/generate_chart.py", "--tickers", args.tickers, "--period", "6mo", "--out", chart_path],
        check=True,
    )
    new_chart_url = upload_media(site, auth, chart_path)

    content = post["content"]["raw"]
    # match any attribute order/extras (e.g. the responsive style="..."
    # publish_wordpress.py adds) rather than requiring the exact original
    # tag shape, so the src swap always lands in place instead of appending
    # a duplicate image when the tag doesn't look exactly as expected.
    pattern = r'<img[^>]*alt="관련 종목 주가 차트"[^>]*/>'

    def swap_src(match):
        return re.sub(r'src="[^"]*"', f'src="{new_chart_url}"', match.group(), count=1)

    new_content, count = re.subn(pattern, swap_src, content, count=1)
    if count == 0:
        new_content = content + f'\n<img src="{new_chart_url}" alt="관련 종목 주가 차트" />\n'
        print("no existing chart <img> found, appended new one instead")

    payload = {"content": new_content}
    if args.publish:
        payload["status"] = "publish"

    resp = requests.post(f"{site}/wp-json/wp/v2/posts/{post['id']}", auth=auth, json=payload, timeout=30)
    resp.raise_for_status()
    updated = resp.json()
    print(f"updated: {updated['link']} (status={updated['status']})")


if __name__ == "__main__":
    main()
