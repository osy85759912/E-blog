#!/usr/bin/env python3
"""Replace the hardcoded "블로그" H1 heading in the given block templates
with new text. Scoped to the exact heading tag so it can't touch anything
else in the template markup."""
import argparse
import re
import os
import sys

import requests

HEADING_PATTERN = re.compile(r'(<h1 class="wp-block-heading has-text-align-left">)블로그(</h1>)')


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-id", required=True, help='e.g. "twentytwentyfive//home"')
    parser.add_argument("--new-text", required=True)
    args = parser.parse_args()

    site, auth = wp_env()

    resp = requests.get(f"{site}/wp-json/wp/v2/templates/{args.template_id}", auth=auth, timeout=30)
    resp.raise_for_status()
    content = resp.json()["content"]["raw"]

    matches = HEADING_PATTERN.findall(content)
    if not matches:
        sys.exit(f"heading pattern not found in {args.template_id!r} -- aborting without changes")
    if len(matches) > 1:
        sys.exit(f"heading pattern found {len(matches)} times in {args.template_id!r} -- ambiguous, aborting")

    new_content = HEADING_PATTERN.sub(lambda m: m.group(1) + args.new_text + m.group(2), content, count=1)

    update_resp = requests.post(
        f"{site}/wp-json/wp/v2/templates/{args.template_id}",
        auth=auth,
        json={"content": new_content},
        timeout=30,
    )
    update_resp.raise_for_status()

    verify = requests.get(f"{site}/wp-json/wp/v2/templates/{args.template_id}", auth=auth, timeout=30)
    verify.raise_for_status()
    ok = args.new_text in verify.json()["content"]["raw"]
    print(f"{args.template_id}: updated={ok}")


if __name__ == "__main__":
    main()
