# FinanceAgent

인공지능 기반 개인용 블룸버그 터미널(PBT) 프로젝트입니다.

## 1. 프로젝트 목적

- 네이버 금융 리포트를 자동 수집하고 PDF 본문을 구조화해 분석 가능한 형태로 저장합니다.
- Voyage 임베딩과 ChromaDB를 활용해 리포트 기반 RAG 검색 자산을 구축합니다.
- Claude를 이용해 리포트를 투자 관점 요약(투자의견/목표주가, 핵심 포인트, 리스크)으로 제공합니다.
- 향후 퀀트 자동화로 확장 가능한 데이터 파이프라인 기반을 마련합니다.

## 2. 프로젝트 구성 (폴더 및 역할)

```text
FinanceAgent/
├── main.py                    # 실행 엔트리포인트 (수집 -> 임베딩 -> 요약)
├── requirements.txt           # Python 의존성
├── .env.example               # 환경변수 샘플
├── src/
│   ├── collectors/            # 네이버 리포트/시세 데이터 수집
│   ├── processors/            # PDF 파싱, 청킹, 임베딩
│   ├── agents/                # 인제션 파이프라인, 요약, RAG 로직
│   ├── storage/               # SQLite/ChromaDB 저장소 핸들러
│   ├── dashboard/             # Streamlit 대시보드
│   └── utils/                 # 설정/로깅/시간 유틸
├── data/
│   ├── report/                # 수집한 원본 PDF 배치 저장
│   ├── stock/                 # 주가 데이터 저장
│   ├── chroma/                # ChromaDB 영속 데이터
│   └── system/                # 크롤링 이력(SQLite)
├── response/
│   └── report/                # Claude 요약 결과(.md, 요약 메타 .json)
└── logs/                      # 일별 실행 로그
```

## 3. 프로젝트 세팅

1) 가상환경 및 패키지 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) 환경변수 파일 준비

```bash
cp .env.example .env
```

3) `.env` 필수/주요 값 설정

- `VOYAGE_API_KEY`: 임베딩 및 벡터 적재에 필수
- `ANTHROPIC_API_KEY`: Claude 요약 생성에 필수
- `PBT_RUN_INGESTION_ON_START`: 시작 시 파이프라인 자동 실행 여부 (`true`/`false`)
- `PBT_NAVER_PAGES_PER_CATEGORY`: 카테고리별 목록 조회 페이지 수
- `PBT_NAVER_MAX_REPORTS`: 1회 실행 시 최대 처리 리포트 수
- `PBT_NAVER_USE_PLAYWRIGHT`: 정적 파싱 실패 시 Playwright fallback 사용 여부

바이트코드 생성 파일(`__pycache__`, `*.pyc`)은 프로젝트 기본 설정으로 생성되지 않도록 구성되어 있습니다.

4) Playwright 사용 시(선택)

```bash
playwright install chromium
```

## 4. 실행

기본 실행:

```bash
python3 main.py
```

옵션 환경변수와 함께 실행 예시:

```bash
PBT_NAVER_PAGES_PER_CATEGORY=2 PBT_NAVER_MAX_REPORTS=12 python3 main.py
```

대시보드 실행:

```bash
streamlit run src/dashboard/app.py
```

## 5. 예상 결과 (예시)

실행이 정상 완료되면 타임스탬프 배치 폴더가 생성됩니다.

- 원문 PDF: `data/report/202602192341/*.pdf`
- 요약 결과: `response/report/202602192341/*.md`
- 실행 요약: `response/report/202602192341/ingestion_summary.json`
- 로그: `logs/20260219.log`

`ingestion_summary.json` 예시:

```json
{
  "started_at": "202602192341",
  "collected_count": 12,
  "processed_count": 2,
  "skipped_duplicate_count": 10,
  "skipped_error_count": 0,
  "report_batch_dir": "/.../data/report/202602192341",
  "response_batch_dir": "/.../response/report/202602192341"
}
```

요약 파일(`*.md`) 예시 구조:

```text
# 종목명 (티커) 리포트 요약
## 1) 투자의견 / 목표주가
## 2) 핵심 포인트 (3줄)
## 3) 리스크 요인
```
