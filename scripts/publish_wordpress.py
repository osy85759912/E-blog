#!/usr/bin/env python3
import argparse
import mimetypes
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


def create_draft_post(site, auth, title, content_html, featured_media_id=None):
    payload = {"title": title, "content": content_html, "status": "draft"}
    if featured_media_id:
        payload["featured_media"] = featured_media_id
    resp = requests.post(f"{site}/wp-json/wp/v2/posts", auth=auth, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--content-file", required=True, help="HTML body")
    parser.add_argument("--image", help="chart image to attach as featured image + embed")
    args = parser.parse_args()

    site, auth = wp_env()

    with open(args.content_file, encoding="utf-8") as f:
        content_html = f.read()

    media_id = None
    if args.image:
        media_id, media_url = upload_media(site, auth, args.image)
        content_html += f'\n<img src="{media_url}" alt="관련 종목 주가 차트" />\n'

    post = create_draft_post(site, auth, args.title, content_html, media_id)
    print(f"draft created: {post['link']} (id={post['id']}, status={post['status']})")
    print(f"edit: {site}/wp-admin/post.php?post={post['id']}&action=edit")


if __name__ == "__main__":
    main()
