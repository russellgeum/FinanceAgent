# FinanceAgent

인공지능 기반 개인용 블룸버그 터미널(PBT) 프로젝트입니다.

## 빠른 시작

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 main.py
```

`main.py` 실행 시 기본적으로 네이버 리포트 수집 -> PDF 텍스트 추출 -> 청킹 ->
Voyage 임베딩 -> Chroma 저장 -> Claude 요약 저장 파이프라인이 동작합니다.

## 환경 변수

- `VOYAGE_API_KEY`: 임베딩 및 벡터 적재에 필수
- `ANTHROPIC_API_KEY`: Claude 요약 생성에 필수
- `PBT_RUN_INGESTION_ON_START`: 시작 시 파이프라인 자동 실행 여부
- `PBT_NAVER_PAGES_PER_CATEGORY`: 카테고리별 목록 조회 페이지 수
- `PBT_NAVER_MAX_REPORTS`: 1회 실행 시 최대 처리 리포트 수
- `PBT_NAVER_USE_PLAYWRIGHT`: 정적 파싱 실패 시 Playwright fallback 사용 여부

## Playwright 사용 시 추가 설정

```bash
playwright install chromium
```

## 대시보드 실행

```bash
streamlit run src/dashboard/app.py
```
