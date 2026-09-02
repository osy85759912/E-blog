#!/usr/bin/env python3
import glob
import os
import subprocess
import sys

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
    tickers = meta["tickers"]
    primary_ticker = tickers.split(",")[0].strip()
    person = meta.get("thumbnail_person")
    base = os.path.splitext(os.path.basename(path))[0]
    chart_path = f"/tmp/{base}.png"
    thumb_path = f"/tmp/{base}-thumb.png"
    content_file = f"/tmp/{base}.html"

    subprocess.run(
        [sys.executable, "scripts/generate_chart.py", "--tickers", tickers, "--period", "6mo", "--out", chart_path],
        check=True,
    )

    thumb_cmd = [sys.executable, "scripts/generate_thumbnail.py", "--ticker", primary_ticker, "--out", thumb_path]
    if person:
        thumb_cmd += ["--person", person]
    thumb_result = subprocess.run(thumb_cmd)
    have_thumb = thumb_result.returncode == 0 and os.path.exists(thumb_path)

    with open(content_file, "w", encoding="utf-8") as f:
        f.write(body)

    publish_cmd = [
        sys.executable,
        "scripts/publish_wordpress.py",
        "--title",
        title,
        "--content-file",
        content_file,
        "--image",
        chart_path,
    ]
    if have_thumb:
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
