#!/usr/bin/env python3
import glob
import os
import re
import subprocess
import sys

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

PENDING_DIR = "pending"
PUBLISHED_DIR = "published"


def parse_frontmatter(text):
    if not text.startswith("---"):
        sys.exit("draft file missing --- frontmatter block")
    _, fm, body = text.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body.strip()


def process(path):
    with open(path, encoding="utf-8") as f:
        meta, body = parse_frontmatter(f.read())

    title = meta["title"]
    tickers = meta.get("tickers")
    category = meta.get("category", "미국주식")
    person = meta.get("thumbnail_person")
    mood = meta.get("mood", "중립")
    base = os.path.splitext(os.path.basename(path))[0]
    content_file = f"/tmp/{base}.html"

    with open(content_file, "w", encoding="utf-8") as f:
        f.write(body)

    publish_cmd = [
        sys.executable,
        "scripts/publish_wordpress.py",
        "--title",
        title,
        "--content-file",
        content_file,
        "--category",
        category,
    ]

    if tickers:
        primary_ticker = tickers.split(",")[0].strip()
        chart_path = f"/tmp/{base}.png"
        thumb_path = f"/tmp/{base}-thumb.png"

        subprocess.run(
            [sys.executable, "scripts/generate_chart.py", "--tickers", tickers, "--period", "6mo", "--out", chart_path],
            check=True,
        )
        publish_cmd += ["--image", chart_path]

        market = "kr" if category == "국내주식" else "us"
        date_match = DATE_RE.search(base)
        thumb_cmd = [
            sys.executable,
            "scripts/generate_thumbnail.py",
            "--ticker",
            primary_ticker,
            "--title",
            title,
            "--mood",
            mood,
            "--market",
            market,
            "--out",
            thumb_path,
        ]
        if date_match:
            thumb_cmd += ["--date", date_match.group(1)]
        if person:
            thumb_cmd += ["--person", person]
        thumb_result = subprocess.run(thumb_cmd)
        if thumb_result.returncode == 0 and os.path.exists(thumb_path):
            publish_cmd += ["--thumbnail", thumb_path]

    subprocess.run(publish_cmd, check=True)


def main():
    os.makedirs(PUBLISHED_DIR, exist_ok=True)
    files = sorted(glob.glob(f"{PENDING_DIR}/*.md"))
    if not files:
        print("no pending drafts")
        return

    for path in files:
        process(path)
        os.rename(path, os.path.join(PUBLISHED_DIR, os.path.basename(path)))
        print(f"processed {path}")


if __name__ == "__main__":
    main()
