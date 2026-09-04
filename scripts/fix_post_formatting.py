#!/usr/bin/env python3
"""One-off: retrofit a post published before the emoji-heading and
chart-in-section conventions -- adds an emoji to each <h3> heading and
moves the "관련 종목 주가 차트" <img> from wherever it sits (typically
appended at the very end) to right after the caption paragraph in the
차트로 보면 section."""
import argparse
import os
import re
import sys

import requests

HEADING_EMOJIS = [
    ("무슨 일이냐면", "🧐"),
    ("배경/맥락", "🔍"),
    ("왜 눈에 띄었냐면", "👀"),
    ("차트로 보면", "📊"),
    ("내 생각", "💬"),
]


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

    for text, emoji in HEADING_EMOJIS:
        old = f"<h3>{text}</h3>"
        new = f"<h3>{emoji} {text}</h3>"
        if old in content:
            content = content.replace(old, new, 1)

    chart_match = re.search(r'<img[^>]*alt="관련 종목 주가 차트"[^>]*/>', content)
    if chart_match:
        chart_tag = chart_match.group()
        without_chart = content[: chart_match.start()] + content[chart_match.end() :]
        h3_match = re.search(r"<h3>[^<]*차트로 보면</h3>", without_chart)
        if h3_match:
            p_end = without_chart.find("</p>", h3_match.end())
            if p_end != -1:
                insert_at = p_end + len("</p>")
                content = without_chart[:insert_at] + "\n" + chart_tag + without_chart[insert_at:]
            else:
                print("[warn] no </p> found after 차트로 보면 heading, leaving chart position unchanged")
        else:
            print("[warn] no 차트로 보면 heading found, leaving chart position unchanged")
    else:
        print("[warn] no chart <img> found in content")

    update_resp = requests.post(f"{site}/wp-json/wp/v2/posts/{args.post_id}", auth=auth, json={"content": content}, timeout=30)
    update_resp.raise_for_status()
    print(f"updated post id={args.post_id}")


if __name__ == "__main__":
    main()
