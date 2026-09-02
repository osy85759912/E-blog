#!/usr/bin/env python3
"""One-off cleanup: trash the WordPress draft posts created while testing the pipeline."""
import html
import os
import sys

import requests

TEST_TITLES = {
    "자동화 테스트 - 무시해주세요",
    "자동화 테스트 2차 - 무시해주세요",
    "자동화 테스트 3차 - 무시해주세요",
    "팀 쿡 15년 만에 떠난 날, 애플 주가는 왜 2.61% 올랐을까",
}


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def main():
    site, auth = wp_env()
    resp = requests.get(
        f"{site}/wp-json/wp/v2/posts",
        auth=auth,
        params={"status": "draft,publish,pending,future", "per_page": 100},
        timeout=30,
    )
    resp.raise_for_status()
    posts = resp.json()

    for post in posts:
        title = html.unescape(post["title"]["rendered"])
        if title in TEST_TITLES:
            del_resp = requests.delete(
                f"{site}/wp-json/wp/v2/posts/{post['id']}",
                auth=auth,
                timeout=30,
            )
            del_resp.raise_for_status()
            print(f"trashed: {title} (id={post['id']})")


if __name__ == "__main__":
    main()
