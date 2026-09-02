#!/usr/bin/env python3
"""One-off setup: create the pages required for AdSense review
(Privacy Policy, About, Contact) via the WordPress REST API. Idempotent —
updates the page if one with the same title already exists."""
import os
import sys

import requests

SITE_NAME = "brotheroh"
CONTACT_EMAIL = "contact@brotheroh.com"

PRIVACY_POLICY = f"""
<p>{SITE_NAME}({{site}})은 방문자의 개인정보를 소중히 다룹니다. 이 개인정보처리방침은 이 사이트를 이용하는 동안 수집되는 정보와 그 사용 방식을 설명합니다.</p>

<h3>쿠키와 광고</h3>
<p>이 사이트는 Google AdSense를 포함한 제3자 광고 서비스를 사용합니다. Google을 비롯한 제3자 공급업체는 쿠키를 사용하여 사용자가 이 사이트 및 다른 사이트를 방문한 기록을 기반으로 광고를 게재합니다.</p>
<p>Google의 광고 쿠키 사용으로 인해 Google과 파트너는 사용자가 이 사이트 또는 다른 사이트를 방문한 정보를 바탕으로 광고를 게재할 수 있습니다. 사용자는 <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google 광고 설정 페이지</a>에서 맞춤 광고를 위한 쿠키 사용을 원하지 않도록 설정할 수 있습니다.</p>

<h3>수집하는 정보</h3>
<p>이 사이트는 별도의 회원가입 없이 이용할 수 있으며, 댓글 작성 시 입력한 이름·이메일 등 최소한의 정보 외에는 방문자로부터 개인정보를 직접 수집하지 않습니다. 다만 Google Analytics 등 방문 통계 도구를 사용할 경우 접속 기기, 브라우저 정보, 방문 페이지 등이 비식별 형태로 수집될 수 있습니다.</p>

<h3>문의</h3>
<p>개인정보처리방침에 대해 문의사항이 있으시면 <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>로 연락 주시기 바랍니다.</p>

<p>본 방침은 관련 법령 또는 서비스 변경에 따라 사전 고지 없이 수정될 수 있습니다.</p>
""".strip()

ABOUT = f"""
<p>안녕하세요, {SITE_NAME} 블로그입니다.</p>

<p>이 블로그는 두 갈래로 운영됩니다.</p>

<p>하나는 <strong>새벽 미국 증시에서 있었던 이슈와 화제거리를 개인적인 시각으로 정리하는 글</strong>입니다. 애널리스트 리포트가 아니라, 매일 새벽 미국장을 챙겨보는 한 개인 투자자가 인상 깊었던 사건을 골라 배경과 개인적인 생각을 담아 씁니다. 투자자문이 아닌 개인 의견이며, 이 점은 매 글 하단에도 명시하고 있습니다.</p>

<p>다른 하나는 <strong>육아·맛집·여행 등 소소한 일상 기록</strong>입니다. 거창한 정보성 콘텐츠라기보다는, 실제로 겪은 일들을 편하게 남기는 공간입니다.</p>

<p>문의사항이 있으시면 <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>로 연락 주세요.</p>
""".strip()

CONTACT = f"""
<p>블로그 관련 문의, 제휴, 오류 제보 등은 아래 이메일로 연락 주세요.</p>

<p><strong>이메일: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></strong></p>

<p>가능한 빠르게 답변드리겠습니다.</p>
""".strip()

PAGES = {
    "개인정보처리방침": PRIVACY_POLICY,
    "소개": ABOUT,
    "문의": CONTACT,
}


def wp_env():
    site = os.environ.get("WP_SITE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME")
    app_password = os.environ.get("WP_APP_PASSWORD")
    if not (site and user and app_password):
        sys.exit("missing WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD env vars")
    return site, (user, app_password)


def find_page_id(site, auth, title):
    resp = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        auth=auth,
        params={"search": title, "per_page": 100, "status": "any"},
        timeout=30,
    )
    resp.raise_for_status()
    for page in resp.json():
        if page["title"]["rendered"] == title:
            return page["id"]
    return None


def main():
    site, auth = wp_env()
    for title, content_template in PAGES.items():
        content = content_template.format(site=site)
        page_id = find_page_id(site, auth, title)
        payload = {"title": title, "content": content, "status": "publish"}
        if page_id:
            resp = requests.post(f"{site}/wp-json/wp/v2/pages/{page_id}", auth=auth, json=payload, timeout=30)
            action = "updated"
        else:
            resp = requests.post(f"{site}/wp-json/wp/v2/pages", auth=auth, json=payload, timeout=30)
            action = "created"
        resp.raise_for_status()
        page = resp.json()
        print(f"{action}: {title} -> {page['link']}")


if __name__ == "__main__":
    main()
