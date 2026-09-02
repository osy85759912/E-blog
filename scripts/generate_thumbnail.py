#!/usr/bin/env python3
"""Generate a news-style split thumbnail: brand-color panel with a clean
vector company logo (Simple Icons) on one side, a Wikimedia Commons photo
of a named person (filtered to explicitly CC/public-domain licensed images
only -- never a scraped press photo) on the other, and a bold caption bar
with the post title across the bottom."""
import argparse
import io
import os
import re
import sys

import cairosvg
import requests
import yfinance as yf
from PIL import Image, ImageDraw, ImageFont, ImageOps

CANVAS_SIZE = (1200, 630)
BRAND_GREEN = (22, 138, 76)
FALLBACK_PANEL = (12, 90, 50)
BAR_BG = (10, 22, 16)
WHITE = (255, 255, 255)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "brotheroh-blog-thumbnail/1.0 (contact: osy85759912@gmail.com)"}
SAFE_LICENSE_MARKERS = ("cc0", "cc by", "public domain", "pd ", "pd-", "cc zero")

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]

COMPANY_SUFFIXES = (" incorporated", " corporation", " company", " group", " holdings", " plc", " inc", " co", " ltd")


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def slugify_company(name):
    name = re.sub(r"[,.]", "", name.lower()).strip()
    for suffix in COMPANY_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
    return name.replace(" ", "")


def company_name_for_ticker(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName")
    except Exception as exc:
        print(f"[thumbnail] company_name_for_ticker({ticker}) failed: {exc!r}", file=sys.stderr)
        return None


def domain_for_ticker(ticker):
    try:
        info = yf.Ticker(ticker).info
        website = info.get("website")
        if website:
            return website.split("//")[-1].split("/")[0].replace("www.", "")
    except Exception:
        pass
    return None


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept": "image/svg+xml,image/*,*/*;q=0.8",
}


def fetch_simple_icon(slug, color="ffffff"):
    url = f"https://cdn.simpleicons.org/{slug}/{color}"
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
        print(f"[thumbnail] {url} -> {resp.status_code}", file=sys.stderr)
        if resp.status_code == 200 and b"<svg" in resp.content[:200]:
            png_bytes = cairosvg.svg2png(bytestring=resp.content, output_width=640, output_height=640)
            return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    except Exception as exc:
        print(f"[thumbnail] fetch_simple_icon({slug}) failed: {exc!r}", file=sys.stderr)
    return None


def fetch_favicon(domain):
    if not domain:
        return None
    for url in (
        f"https://icons.duckduckgo.com/ip3/{domain}.ico",
        f"https://www.google.com/s2/favicons?domain={domain}&sz=256",
    ):
        try:
            resp = requests.get(url, timeout=15)
            print(f"[thumbnail] {url} -> {resp.status_code}", file=sys.stderr)
            if resp.status_code == 200 and resp.content:
                return Image.open(io.BytesIO(resp.content)).convert("RGBA")
        except Exception as exc:
            print(f"[thumbnail] fetch_favicon via {url} failed: {exc!r}", file=sys.stderr)
    return None


def fetch_logo(ticker):
    name = company_name_for_ticker(ticker)
    slugs = []
    if name:
        slugs.append(slugify_company(name))
    slugs.append(ticker.lower())
    for slug in dict.fromkeys(slugs):
        icon = fetch_simple_icon(slug)
        if icon:
            return icon
    print("[thumbnail] no simple-icon match, falling back to favicon", file=sys.stderr)
    return fetch_favicon(domain_for_ticker(ticker))


def find_commons_photo(person_name):
    try:
        search = requests.get(
            COMMONS_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"{person_name} portrait filetype:bitmap",
                "srnamespace": 6,
                "format": "json",
                "srlimit": 5,
            },
            headers=HEADERS,
            timeout=15,
        ).json()
        candidates = [r["title"] for r in search.get("query", {}).get("search", [])]
        print(f"[thumbnail] commons candidates for {person_name!r}: {candidates}", file=sys.stderr)
    except Exception as exc:
        print(f"[thumbnail] commons search failed: {exc!r}", file=sys.stderr)
        return None

    for title in candidates:
        try:
            info = requests.get(
                COMMONS_API,
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata",
                    "format": "json",
                },
                headers=HEADERS,
                timeout=15,
            ).json()
            page = next(iter(info.get("query", {}).get("pages", {}).values()))
            imageinfo = (page.get("imageinfo") or [None])[0]
            if not imageinfo:
                continue
            license_raw = imageinfo.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "").lower()
            license_short = license_raw.replace("-", " ")
            print(f"[thumbnail] {title!r} license={license_raw!r}", file=sys.stderr)
            if not any(marker in license_short for marker in SAFE_LICENSE_MARKERS):
                continue
            img_resp = requests.get(imageinfo["url"], headers=HEADERS, timeout=20)
            if img_resp.status_code == 200:
                return Image.open(io.BytesIO(img_resp.content)).convert("RGBA")
        except Exception as exc:
            print(f"[thumbnail] checking {title!r} failed: {exc!r}", file=sys.stderr)
            continue
    return None


def wrap_text(draw, text, font, max_width, max_lines=2):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)

    consumed = len(" ".join(lines))
    if consumed < len(text) and lines:
        last = lines[-1]
        while draw.textlength(last + "…", font=font) > max_width and len(last) > 1:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines[:max_lines]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True, help="primary ticker, used to look up the company logo")
    parser.add_argument("--person", help="person name to look up on Wikimedia Commons (optional)")
    parser.add_argument("--title", required=True, help="post title, shown as a bold caption across the bottom")
    parser.add_argument("--badge", default="브라더오", help="small top-left brand badge text")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    half = CANVAS_SIZE[0] // 2
    canvas = Image.new("RGB", CANVAS_SIZE, BRAND_GREEN).convert("RGBA")

    person_img = find_commons_photo(args.person) if args.person else None
    if person_img:
        fitted = ImageOps.fit(person_img.convert("RGB"), (half, CANVAS_SIZE[1]), Image.LANCZOS)
        canvas.paste(fitted, (half, 0))
    else:
        ImageDraw.Draw(canvas).rectangle([half, 0, CANVAS_SIZE[0], CANVAS_SIZE[1]], fill=FALLBACK_PANEL)

    logo_img = fetch_logo(args.ticker)
    if logo_img:
        logo_fit = ImageOps.contain(logo_img, (340, 340))
        lx = (half - logo_fit.width) // 2
        ly = (CANVAS_SIZE[1] - logo_fit.height) // 2 - 20
        canvas.paste(logo_fit, (lx, ly), logo_fit)

    draw = ImageDraw.Draw(canvas)

    badge_font = load_font(30)
    pad_x, pad_y = 18, 10
    badge_w = draw.textlength(args.badge, font=badge_font) + pad_x * 2
    badge_h = 30 + pad_y * 2
    draw.rounded_rectangle([28, 28, 28 + badge_w, 28 + badge_h], radius=10, fill=WHITE)
    draw.text((28 + pad_x, 28 + pad_y - 2), args.badge, font=badge_font, fill=BRAND_GREEN)

    bar_h = 190
    draw.rectangle([0, CANVAS_SIZE[1] - bar_h, CANVAS_SIZE[0], CANVAS_SIZE[1]], fill=BAR_BG)
    cap_font = load_font(50)
    lines = wrap_text(draw, args.title, cap_font, CANVAS_SIZE[0] - 80, max_lines=2)
    y = CANVAS_SIZE[1] - bar_h + 28
    for line in lines:
        draw.text((40, y), line, font=cap_font, fill=WHITE)
        y += 62

    canvas.convert("RGB").save(args.out, quality=92)
    print(args.out)


if __name__ == "__main__":
    main()
