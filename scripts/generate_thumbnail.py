#!/usr/bin/env python3
"""Generate the featured-image thumbnail: a soft mesh-gradient background
colored by the day's news mood, a bold hero percentage (today's price move),
and a small "glass" logo chip (plus an optional circular portrait medallion)
tucked in the corner -- deliberately minimal, no brand badges or text pills."""
import argparse
import io
import os
import re
import sys

import cairosvg
import numpy as np
import requests
import yfinance as yf
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

CANVAS_SIZE = (1200, 630)
WHITE = (255, 255, 255)

# mood -> base backdrop color, a couple of large soft "mesh" blob colors
# (positioned as fractions of the canvas), and an accent color used for the
# hero number's direction arrow and the caption's accent tick.
MOOD_STYLES = {
    "호재": {
        "base": (8, 35, 32),
        "blobs": [((34, 168, 122), 0.82, 0.12, 520), ((140, 214, 150), 0.12, 0.92, 420)],
        "accent": (120, 235, 175),
    },
    "악재": {
        "base": (42, 16, 15),
        "blobs": [((196, 86, 47), 0.84, 0.14, 520), ((150, 42, 40), 0.14, 0.90, 420)],
        "accent": (240, 152, 108),
    },
    "패닉": {
        "base": (12, 7, 8),
        "blobs": [((112, 24, 27), 0.80, 0.18, 500), ((58, 10, 14), 0.16, 0.88, 420)],
        "accent": (222, 96, 96),
    },
    "중립": {
        "base": (17, 21, 31),
        "blobs": [((90, 103, 140), 0.82, 0.16, 520), ((132, 142, 170), 0.16, 0.90, 420)],
        "accent": (176, 186, 212),
    },
}
DEFAULT_MOOD = "중립"

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "brotheroh-blog-thumbnail/1.0 (contact: osy85759912@gmail.com)"}
SAFE_LICENSE_MARKERS = ("cc0", "cc by", "public domain", "pd ", "pd-", "cc zero")

FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]
FONT_REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
]

COMPANY_SUFFIXES = (" incorporated", " corporation", " company", " group", " holdings", " plc", " inc", " co", " ltd")


def load_font(size, bold=True):
    for path in (FONT_BOLD_CANDIDATES if bold else FONT_REGULAR_CANDIDATES):
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


def fetch_percent_change(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="5d")["Close"]
        if len(hist) < 2:
            return None
        last, prev = hist.iloc[-1], hist.iloc[-2]
        return (last - prev) / prev * 100
    except Exception as exc:
        print(f"[thumbnail] fetch_percent_change({ticker}) failed: {exc!r}", file=sys.stderr)
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


def recolor_to_white(img):
    """Flatten any monochrome icon to solid white, keyed off its alpha silhouette."""
    alpha = img.convert("RGBA").split()[-1]
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.putalpha(alpha)
    return white


SIMPLE_ICON_SOURCES = [
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/{slug}.svg",
    "https://cdn.simpleicons.org/{slug}",
]


def fetch_simple_icon(slug):
    for template in SIMPLE_ICON_SOURCES:
        url = template.format(slug=slug)
        try:
            resp = requests.get(url, timeout=15)
            print(f"[thumbnail] {url} -> {resp.status_code}", file=sys.stderr)
            if resp.status_code == 200 and b"<svg" in resp.content[:200]:
                png_bytes = cairosvg.svg2png(bytestring=resp.content, output_width=640, output_height=640)
                return recolor_to_white(Image.open(io.BytesIO(png_bytes)))
        except Exception as exc:
            print(f"[thumbnail] fetch_simple_icon via {url} failed: {exc!r}", file=sys.stderr)
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


def build_mesh_background(size, style):
    """Soft organic gradient: a flat base tone with a couple of large,
    heavily blurred color blobs blended in -- avoids the flat "PowerPoint"
    look of a plain linear gradient."""
    w, h = size
    canvas = Image.new("RGB", size, style["base"])
    for color, fx, fy, radius in style["blobs"]:
        cx, cy = int(w * fx), int(h * fy)
        layer = Image.new("RGB", size, color)
        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius * 0.6))
        canvas = Image.composite(layer, canvas, mask)
    return canvas


def add_grain(img, amount=9):
    """Subtle film-grain noise so the gradient doesn't look flat/plastic."""
    arr = np.asarray(img).astype(np.int16)
    noise = np.random.randint(-amount, amount + 1, arr.shape[:2] + (1,)).astype(np.int16)
    noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy, mode=img.mode)


def add_vignette(img, strength=0.32):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([-w * 0.25, -h * 0.3, w * 1.25, h * 1.3], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(140))
    mask = ImageOps.invert(mask).point(lambda p: int(p * strength))
    black = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(black, img, mask)


def drop_shadow(size, radius, blur=18, opacity=110):
    """A soft blurred shadow shape, sized to sit behind a chip/medallion."""
    pad = blur * 2
    shadow = Image.new("RGBA", (size[0] + pad * 2, size[1] + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [pad, pad, pad + size[0], pad + size[1]], radius=radius, fill=(0, 0, 0, opacity)
    )
    return shadow.filter(ImageFilter.GaussianBlur(blur)), pad


def glass_chip(logo_img, chip_size=168, logo_size=98):
    """A soft translucent white rounded chip with the logo centered in it."""
    chip = Image.new("RGBA", (chip_size, chip_size), (0, 0, 0, 0))
    ImageDraw.Draw(chip).rounded_rectangle(
        [0, 0, chip_size - 1, chip_size - 1], radius=int(chip_size * 0.28), fill=(255, 255, 255, 235)
    )
    fitted = ImageOps.contain(logo_img, (logo_size, logo_size))
    fx = (chip_size - fitted.width) // 2
    fy = (chip_size - fitted.height) // 2
    chip.paste(fitted, (fx, fy), fitted)
    return chip


def circular_portrait(person_img, diameter=140, ring=(255, 255, 255, 230), ring_width=5):
    # flatten onto white first -- if the source has transparency, fitting it
    # to RGB directly would otherwise leave black fringing around the edge
    rgba = person_img.convert("RGBA")
    flattened = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    flattened.alpha_composite(rgba)
    fitted = ImageOps.fit(flattened.convert("RGB"), (diameter, diameter), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, diameter - 1, diameter - 1], fill=255)
    fitted.putalpha(mask)

    ringed = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    ringed.paste(fitted, (0, 0), fitted)
    ImageDraw.Draw(ringed).ellipse([0, 0, diameter - 1, diameter - 1], outline=ring, width=ring_width)
    return ringed


def paste_with_shadow(canvas, chip, xy, radius, blur=18, opacity=110):
    shadow, pad = drop_shadow((chip.width, chip.height), radius, blur=blur, opacity=opacity)
    canvas.alpha_composite(shadow, (xy[0] - pad, xy[1] - pad + 6))
    canvas.alpha_composite(chip, xy)


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


def draw_text_with_shadow(canvas, xy, text, font, fill=WHITE, shadow_opacity=140, blur=6, offset=(0, 3)):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((xy[0] + offset[0], xy[1] + offset[1]), text, font=font, fill=(0, 0, 0, shadow_opacity))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(layer)
    ImageDraw.Draw(canvas).text(xy, text, font=font, fill=fill)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True, help="primary ticker, used to look up the company logo")
    parser.add_argument("--person", help="person name to look up on Wikimedia Commons (optional)")
    parser.add_argument("--title", required=True, help="post title, shown as a bold caption across the bottom")
    parser.add_argument(
        "--mood",
        default=DEFAULT_MOOD,
        choices=list(MOOD_STYLES.keys()),
        help="news tone, colors the thumbnail (호재/악재/패닉/중립)",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    style = MOOD_STYLES[args.mood]
    canvas = build_mesh_background(CANVAS_SIZE, style)
    canvas = add_grain(canvas, amount=9)
    canvas = add_vignette(canvas, strength=0.30)
    canvas = canvas.convert("RGBA")

    # bottom gradient fade so the title always reads cleanly, whatever sits
    # behind it -- softer than a hard-edged solid caption bar.
    fade_h = int(CANVAS_SIZE[1] * 0.46)
    fade = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    fade_draw = ImageDraw.Draw(fade)
    fade_top = CANVAS_SIZE[1] - fade_h
    for y in range(fade_top, CANVAS_SIZE[1]):
        t = (y - fade_top) / fade_h
        fade_draw.line([(0, y), (CANVAS_SIZE[0], y)], fill=(6, 8, 12, int(220 * t**1.4)))
    canvas.alpha_composite(fade)

    draw = ImageDraw.Draw(canvas)

    # hero stat: today's percent change, top-left
    pct = fetch_percent_change(args.ticker)
    if pct is not None:
        arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "■")
        pct_font = load_font(78)
        arrow_font = load_font(40)
        label_font = load_font(26, bold=False)

        draw_text_with_shadow(canvas, (44, 40), f"{pct:+.1f}%", pct_font, fill=WHITE)
        draw = ImageDraw.Draw(canvas)
        num_w = draw.textlength(f"{pct:+.1f}%", font=pct_font)
        draw_text_with_shadow(canvas, (44 + num_w + 14, 58), arrow, arrow_font, fill=style["accent"])
        draw = ImageDraw.Draw(canvas)
        draw.text((46, 128), "오늘 등락률", font=label_font, fill=(255, 255, 255, 205))

    # supporting brand marks, bottom-right: logo chip (+ optional portrait)
    logo_img = fetch_logo(args.ticker)
    person_img = find_commons_photo(args.person) if args.person else None

    margin = 40
    chip_y = CANVAS_SIZE[1] - margin - 168
    cursor_x = CANVAS_SIZE[0] - margin

    if logo_img:
        chip = glass_chip(logo_img)
        cursor_x -= chip.width
        paste_with_shadow(canvas, chip, (cursor_x, chip_y), radius=int(chip.width * 0.28))
        cursor_x -= 20

    if person_img:
        portrait = circular_portrait(person_img, diameter=140)
        py = chip_y + (168 - portrait.height) // 2
        cursor_x -= portrait.width
        paste_with_shadow(canvas, portrait, (cursor_x, py), radius=portrait.width // 2, blur=16)

    # title caption -- the badge chips sit in the bottom-right corner, in the
    # same vertical band as the caption text, so the wrap width must leave
    # room for them or the last line can run straight under the artwork.
    accent_color = style["accent"]
    cap_font = load_font(46)
    caption_right_edge = cursor_x - 30 if (logo_img or person_img) else CANVAS_SIZE[0] - 40
    max_caption_width = caption_right_edge - 62
    lines = wrap_text(ImageDraw.Draw(canvas), args.title, cap_font, max_caption_width, max_lines=2)
    print(f"[thumbnail] cursor_x={cursor_x} max_caption_width={max_caption_width} lines={lines}", file=sys.stderr)
    line_h = 58
    total_h = line_h * len(lines)
    y = CANVAS_SIZE[1] - 36 - total_h
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([40, y + 4, 46, y + total_h - 10], radius=3, fill=accent_color)
    for line in lines:
        draw_text_with_shadow(canvas, (62, y), line, cap_font, fill=WHITE, blur=8)
        y += line_h

    canvas.convert("RGB").save(args.out, quality=92)
    print(args.out)


if __name__ == "__main__":
    main()
