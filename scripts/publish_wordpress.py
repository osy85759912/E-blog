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


def get_category_id_by_name(site, auth, name):
    resp = requests.get(
        f"{site}/wp-json/wp/v2/categories",
        auth=auth,
        params={"search": name, "per_page": 100},
        timeout=30,
    )
    resp.raise_for_status()
    for category in resp.json():
        if category["name"] == name:
            return category["id"]
    return None


def create_post(site, auth, title, content_html, status, featured_media_id=None, category_id=None):
    payload = {"title": title, "content": content_html, "status": status}
    if featured_media_id:
        payload["featured_media"] = featured_media_id
    if category_id:
        payload["categories"] = [category_id]
    resp = requests.post(f"{site}/wp-json/wp/v2/posts", auth=auth, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--content-file", required=True, help="HTML body")
    parser.add_argument("--image", help="chart image, embedded in the body")
    parser.add_argument("--thumbnail", help="cover/thumbnail image (logo+person composite); used as the featured image")
    parser.add_argument("--category", default="미국주식", help="category name to assign (default: 미국주식)")
    parser.add_argument("--status", default="publish", choices=["publish", "draft"], help="post status (default: publish)")
    args = parser.parse_args()

    site, auth = wp_env()

    with open(args.content_file, encoding="utf-8") as f:
        content_html = f.read()

    img_style = "max-width:100%;height:auto;display:block;margin:16px auto;"

    thumb_id = None
    if args.thumbnail:
        thumb_id, thumb_url = upload_media(site, auth, args.thumbnail)
        content_html = f'<img src="{thumb_url}" alt="{args.title}" style="{img_style}" />\n' + content_html

    chart_id = None
    if args.image:
        chart_id, chart_url = upload_media(site, auth, args.image)
        chart_tag = f'<img src="{chart_url}" alt="관련 종목 주가 차트" style="{img_style}" />'
        chart_marker = "<!-- CHART -->"
        if chart_marker in content_html:
            content_html = content_html.replace(chart_marker, chart_tag, 1)
        else:
            content_html += f"\n{chart_tag}\n"

    category_id = get_category_id_by_name(site, auth, args.category) if args.category else None

    post = create_post(site, auth, args.title, content_html, args.status, thumb_id or chart_id, category_id)
    print(f"post created: {post['link']} (id={post['id']}, status={post['status']})")
    print(f"edit: {site}/wp-admin/post.php?post={post['id']}&action=edit")


if __name__ == "__main__":
    main()
