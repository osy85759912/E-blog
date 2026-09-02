# E-blog — 미국장 새벽 이슈 요약 블로그 자동화

새벽 미국 증시 이슈·가십을 요약해 워드프레스에 초안으로 올리는 자동화 파이프라인입니다.
매일 아침 이 환경의 예약 트리거(Routine)가 초안 글을 작성해 저장소에 커밋하고, GitHub Actions가 차트 생성·워드프레스 업로드를 처리합니다.
사용자는 검토 후 워드프레스 관리자 화면에서 직접 발행 버튼을 누릅니다.
(완전 무인 발행이 아닌, 초안 자동생성 + 발행 전 사람 확인 구조입니다 — 이유는 `docs/ROUTINE_PROMPT.md` 참고)

두 단계로 나뉜 이유: Claude가 실행되는 환경은 보안상 외부 사이트로 직접 나갈 수 없습니다. 그래서 뉴스 조사·글쓰기는 Claude가, 실제 네트워크 호출(주가 데이터, 워드프레스 API)이 필요한 부분은 GitHub Actions(제한 없는 일반 러너)가 나눠서 처리합니다.

## 하루 흐름

1. 예약 트리거가 08:00 KST경 실행됨
2. 새벽 미국장 관련 뉴스/이슈/가십을 웹 검색으로 수집
3. `docs/style_guide.md` 톤에 맞춰 글 초안 작성 (제목은 클릭률 공식 적용), 관련 티커 선정
4. `pending/<날짜>.md`로 커밋·푸시 (형식은 `docs/ROUTINE_PROMPT.md` 참고)
5. 그 푸시가 `.github/workflows/publish-draft.yml`을 트리거 → GitHub Actions가 `scripts/generate_chart.py`로 차트 생성 후 `scripts/publish_wordpress.py`로 워드프레스에 **초안(draft)** 업로드, 처리된 파일은 `published/`로 이동
6. 사용자에게 푸시 알림으로 검토 요청 → 사용자가 워드프레스 관리자 화면에서 확인 후 발행 버튼 클릭

## 당신이 준비해야 할 것 (제가 대신 결제/가입/설정할 수 없는 부분)

1. **호스팅 + 도메인 구매, 워드프레스 설치** — 완료 (brotheroh.com, 카페24)
2. **Application Password 발급** — 완료
3. **GitHub 저장소에 Secrets 등록** (GitHub Actions가 이 값들로 워드프레스에 접속합니다)
   - `https://github.com/osy85759912/E-blog` → 상단 **Settings** 탭 → 왼쪽 메뉴 **Secrets and variables → Actions** → **New repository secret**
   - 아래 3개를 각각 이름/값으로 등록:
     - `WP_SITE_URL` → `https://brotheroh.com`
     - `WP_USERNAME`
     - `WP_APP_PASSWORD`
   - (코드나 커밋에는 절대 이 값들을 넣지 않습니다 — GitHub Secrets에만 등록)

세 Secret이 등록되면 알려주세요 — 예약 트리거(Routine)를 실제로 활성화하겠습니다. 그 전까지는 아무것도 자동 발행되지 않습니다.

## 구성

- `docs/style_guide.md` — 글 톤/페르소나, 제목 공식, 필수 디스클레이머 문구
- `docs/ROUTINE_PROMPT.md` — 예약 트리거가 매일 수행할 지시문 원본
- `pending/` — Routine이 커밋하는 초안 파일 (frontmatter + 본문 HTML)
- `published/` — Actions가 처리 완료 후 옮겨두는 초안 파일
- `.github/workflows/publish-draft.yml` — pending/ 변경을 감지해 차트 생성 + 워드프레스 업로드를 실행하는 워크플로
- `scripts/generate_chart.py` — 종목/섹터 주가 차트 PNG 생성 (yfinance, 무료)
- `scripts/publish_wordpress.py` — 워드프레스 REST API로 초안 업로드
- `scripts/process_pending_draft.py` — 위 두 스크립트를 pending/ 파일 기준으로 실행하는 오케스트레이터 (Actions에서 호출)

## 로컬 테스트

```bash
pip install -r requirements.txt
python scripts/generate_chart.py --tickers NVDA,SMCI --period 6mo --out /tmp/chart.png
WP_SITE_URL=... WP_USERNAME=... WP_APP_PASSWORD=... \
  python scripts/publish_wordpress.py --title "테스트" --content-file body.html --image /tmp/chart.png
```
