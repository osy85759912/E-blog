# E-blog — 미국장 새벽 이슈 요약 블로그 자동화

새벽 미국 증시 이슈·가십을 요약해 워드프레스에 초안으로 올리는 자동화 파이프라인입니다.
매일 아침 이 환경의 예약 트리거(Routine)가 실행되어 초안을 만들고, 사용자가 검토 후 직접 발행합니다.
(완전 무인 발행이 아닌, 초안 자동생성 + 발행 전 사람 확인 구조입니다 — 이유는 `docs/ROUTINE_PROMPT.md` 참고)

## 하루 흐름

1. 예약 트리거가 08:00 KST경 실행됨
2. 새벽 미국장 관련 뉴스/이슈/가십을 웹 검색으로 수집
3. `docs/style_guide.md` 톤에 맞춰 글 초안 작성 (제목은 클릭률 공식 적용)
4. 관련 종목/섹터 주가 차트를 `scripts/generate_chart.py`로 생성
5. `scripts/publish_wordpress.py`로 워드프레스에 **초안(draft)** 상태로 업로드
6. 사용자에게 푸시 알림으로 검토 요청 → 사용자가 워드프레스 관리자 화면에서 확인 후 발행 버튼 클릭

## 당신이 준비해야 할 것 (제가 대신 결제/가입할 수 없는 부분)

비용 절감을 위해 워드프레스닷컴 대신 **저가 셀프호스팅**으로 진행합니다 (월 $3~5대 호스팅 + 도메인). Application Password/REST API는 워드프레스 코어 기능이라 어떤 호스팅사를 쓰든 동일하게 동작하고, 아래 스크립트도 수정 없이 그대로 씁니다.

1. **호스팅 + 도메인 구매, 워드프레스 설치**
   - 저가 호스팅사(Hostinger, 가비아, Cafe24 등)에서 호스팅 구매 → 대부분 "1-클릭 워드프레스 설치" 기능 제공
   - 호스팅사 프로모션에 도메인이 포함돼 있는 경우가 많으니 확인
2. **Application Password 발급**
   - 워드프레스 관리자 로그인 → 사용자(Users) → 프로필(Profile) → 하단 "Application Passwords" 섹션
   - 이름을 `e-blog-automation`으로 새 비밀번호 생성 → 공백 포함된 문자열이 발급됨 (계정 로그인 비밀번호와 다름, 나중에 개별 폐기 가능)
3. 아래 3개 값을 **이 환경의 환경변수/시크릿 설정**에 등록 (코드나 커밋에는 절대 넣지 않습니다)
   - `WP_SITE_URL` (예: `https://yourblog.com`)
   - `WP_USERNAME`
   - `WP_APP_PASSWORD`

세 값이 준비되면 알려주세요 — 예약 트리거(Routine)를 실제로 활성화하겠습니다. 그 전까지는 스크립트만 준비된 상태이며 아무것도 자동 발행되지 않습니다.

## 구성

- `docs/style_guide.md` — 글 톤/페르소나, 제목 공식, 필수 디스클레이머 문구
- `docs/ROUTINE_PROMPT.md` — 예약 트리거가 매일 수행할 지시문 원본
- `scripts/generate_chart.py` — 종목/섹터 주가 차트 PNG 생성 (yfinance, 무료)
- `scripts/publish_wordpress.py` — 워드프레스 REST API로 초안 업로드

## 로컬 테스트

```bash
pip install -r requirements.txt
python scripts/generate_chart.py --tickers NVDA,SMCI --period 6mo --out /tmp/chart.png
WP_SITE_URL=... WP_USERNAME=... WP_APP_PASSWORD=... \
  python scripts/publish_wordpress.py --title "테스트" --content-file body.html --image /tmp/chart.png
```
