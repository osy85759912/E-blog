#!/usr/bin/env python3
"""Debug helper: dump full Commons imageinfo/extmetadata for given file titles."""
import argparse
import json

import requests

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "brotheroh-blog-thumbnail/1.0 (contact: osy85759912@gmail.com)"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--titles", required=True, help="pipe-separated File: titles")
    args = parser.parse_args()

    resp = requests.get(
        COMMONS_API,
        params={
            "action": "query",
            "titles": args.titles,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        },
        headers=HEADERS,
        timeout=20,
    )
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
