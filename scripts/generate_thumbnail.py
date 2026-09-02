#!/usr/bin/env python3
"""Generate a featured-image thumbnail from a company logo (Clearbit) and,
optionally, a Wikimedia Commons photo of a named person filtered to
explicitly CC/public-domain licensed images only (never scraped press photos)."""
import argparse
import io
import sys

import requests
import yfinance as yf
from PIL import Image, ImageDraw, ImageOps

CANVAS_SIZE = (1200, 630)
BG_TOP = (233, 251, 241)
BG_BOTTOM = (201, 243, 221)
CARD_WHITE = (255, 255, 255, 255)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "brotheroh-blog-thumbnail/1.0 (contact: osy85759912@gmail.com)"}

SAFE_LICENSE_MARKERS = ("cc0", "cc-by", "public domain", "pd-", "cc-zero")


def domain_for_ticker(ticker):
    try:
        info = yf.Ticker(ticker).info
        website = info.get("website")
        if website:
            return website.split("//")[-1].split("/")[0].replace("www.", "")
    except Exception:
        pass
    return None


def fetch_logo(domain):
    if not domain:
        return None
    try:
        resp = requests.get(f"https://logo.clearbit.com/{domain}", timeout=15)
        if resp.status_code == 200 and resp.content:
            return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        pass
    return None


def find_commons_photo(person_name):
    try:
        search = requests.get(
            COMMONS_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"{person_name} portrait",
                "srnamespace": 6,
                "format": "json",
                "srlimit": 5,
            },
            headers=HEADERS,
            timeout=15,
        ).json()
        candidates = [r["title"] for r in search.get("query", {}).get("search", [])]
    except Exception:
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
            license_short = imageinfo.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "").lower()
            if not any(marker in license_short for marker in SAFE_LICENSE_MARKERS):
                continue
            img_resp = requests.get(imageinfo["url"], headers=HEADERS, timeout=20)
            if img_resp.status_code == 200:
                return Image.open(io.BytesIO(img_resp.content)).convert("RGBA")
        except Exception:
            continue
    return None


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), size], radius=radius, fill=255)
    return mask


def paste_rounded(base, img, box, radius):
    fitted = ImageOps.fit(img.convert("RGBA"), (box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
    base.paste(fitted, box[:2], rounded_mask(fitted.size, radius))


def build_gradient(size, top, bottom):
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / size[1]
        draw.line([(0, y), (size[0], y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True, help="primary ticker, used to look up the company logo")
    parser.add_argument("--person", help="person name to look up on Wikimedia Commons (optional)")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    canvas = build_gradient(CANVAS_SIZE, BG_TOP, BG_BOTTOM).convert("RGBA")

    person_img = find_commons_photo(args.person) if args.person else None
    logo_img = fetch_logo(domain_for_ticker(args.ticker))

    if not person_img and not logo_img:
        sys.exit("no logo or licensed person photo found")

    if person_img:
        paste_rounded(canvas, person_img, (90, 105, 90 + 420, 105 + 420), radius=28)

    if logo_img:
        chip_size = (170, 170) if person_img else (220, 220)
        chip_pos = (CANVAS_SIZE[0] - chip_size[0] - 60, CANVAS_SIZE[1] - chip_size[1] - 60)
        chip = Image.new("RGBA", chip_size, CARD_WHITE)
        canvas.paste(chip, chip_pos, rounded_mask(chip_size, 32))
        logo_fit = ImageOps.contain(logo_img, (chip_size[0] - 50, chip_size[1] - 50))
        lx = chip_pos[0] + (chip_size[0] - logo_fit.width) // 2
        ly = chip_pos[1] + (chip_size[1] - logo_fit.height) // 2
        canvas.paste(logo_fit, (lx, ly), logo_fit)

    canvas.convert("RGB").save(args.out, quality=90)
    print(args.out)


if __name__ == "__main__":
    main()
