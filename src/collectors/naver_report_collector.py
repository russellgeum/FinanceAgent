"""네이버 금융 리포트 수집 모듈."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from bs4.element import Tag


@dataclass(slots=True)
class ReportSource:
    """
    네이버 리포트의 핵심 메타데이터를 보관한다.

    Args:
        title (str): 리포트 제목.
        url (str): 상세 페이지 URL.
        category (str): 카테고리(company/industry/market).
        date (str): 기준 일자(YYYYMMDD).
        ticker (str): 종목 코드, 없으면 MARKET.

    Returns:
        None: 수집 항목 데이터 객체를 생성한다.
    """

    title: str
    url: str
    category: str
    date: str
    ticker: str




class NaverReportCollector:
    """
    네이버 금융 리서치 목록과 PDF를 수집하는 크롤러.

    Args:
        timeout_seconds (int): HTTP 요청 타임아웃(초).
        use_playwright (bool): 정적 요청 실패 시 Playwright 사용 여부.

    Returns:
        None: 크롤러 객체를 생성한다.
    """

    _BASE_URL: str = "https://finance.naver.com/research/"
    _LIST_PATHS: dict[str, str] = {
        "company": "company_list.naver",
        "industry": "industry_list.naver",
        "market": "invest_list.naver",
    }

    def __init__(
        self,
        timeout_seconds: int = 15,
        use_playwright: bool = False,
    ) -> None:
        self._timeout_seconds: int = timeout_seconds
        self._use_playwright: bool = use_playwright
        self._user_agent: str = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )

    def fetch_report_sources(self, pages_per_category: int = 1) -> list[ReportSource]:
        """
        카테고리별 최근 리포트 목록을 수집한다.

        Args:
            pages_per_category (int): 카테고리당 탐색할 페이지 수.

        Returns:
            list[ReportSource]: 중복 제거된 리포트 메타 목록.
        """
        if pages_per_category < 1:
            raise ValueError("pages_per_category는 1 이상이어야 합니다.")

        gathered: list[ReportSource] = []
        seen_urls: set[str] = set()

        for category, path in self._LIST_PATHS.items():
            for page in range(1, pages_per_category + 1):
                list_url: str = f"{self._BASE_URL}{path}?page={page}"
                try:
                    html: str = self._fetch_html(list_url)
                except RuntimeError:
                    continue
                page_items: list[ReportSource] = self._parse_list_page(
                    html=html,
                    category=category,
                    fallback_date=self._today_yyyymmdd(),
                )
                for item in page_items:
                    if item.url in seen_urls:
                        continue
                    seen_urls.add(item.url)
                    gathered.append(item)

        return gathered

    def resolve_pdf_url(self, detail_url: str) -> str | None:
        """
        상세 페이지에서 PDF 원문 URL을 추출한다.

        Args:
            detail_url (str): 리포트 상세 페이지 URL.

        Returns:
            str | None: PDF URL, 찾지 못하면 None.
        """
        html: str = self._fetch_html(detail_url)
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.select("a[href]"):
            href: str = str(link.get("href", "")).strip()
            normalized: str = href.lower()
            if ".pdf" in normalized:
                return urljoin(detail_url, href)

            link_text: str = link.get_text(" ", strip=True).lower()
            if "원문" in link_text and href:
                maybe_pdf: str = urljoin(detail_url, href)
                if ".pdf" in maybe_pdf.lower():
                    return maybe_pdf

        direct_match = re.search(
            r"(https?://[^\"'\s]+\.pdf)",
            html,
            flags=re.IGNORECASE,
        )
        if direct_match:
            return direct_match.group(1)

        relative_match = re.search(r"(/[^\"'\s]+\.pdf)", html, flags=re.IGNORECASE)
        if relative_match:
            return urljoin(detail_url, relative_match.group(1))

        return None

    def download_pdf(self, pdf_url: str, destination: Path) -> Path:
        """
        PDF 파일을 지정한 로컬 경로로 저장한다.

        Args:
            pdf_url (str): PDF 원문 URL.
            destination (Path): 저장할 파일 경로.

        Returns:
            Path: 저장 완료된 파일 경로.
        """
        content: bytes = self._download_binary(pdf_url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return destination

    def _fetch_html(self, url: str) -> str:
        """
        URL에서 HTML 문서를 가져온다.

        Args:
            url (str): 요청 대상 URL.

        Returns:
            str: UTF-8 디코딩된 HTML 문자열.
        """
        try:
            return self._fetch_html_static(url)
        except RuntimeError:
            if self._use_playwright:
                return self._fetch_html_playwright(url)
            raise

    def _fetch_html_static(self, url: str) -> str:
        """
        urllib 기반 정적 요청으로 HTML을 조회한다.

        Args:
            url (str): 요청 대상 URL.

        Returns:
            str: UTF-8 디코딩된 HTML 문자열.
        """
        request = Request(
            url=url,
            headers={
                "User-Agent": self._user_agent,
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
            },
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                raw: bytes = response.read()
                charset: str = response.headers.get_content_charset() or "euc-kr"
                return raw.decode(charset, errors="ignore")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"HTML 조회 실패: url={url}, reason={exc}") from exc

    def _fetch_html_playwright(self, url: str) -> str:
        """
        Playwright를 사용해 동적으로 렌더링된 HTML을 가져온다.

        Args:
            url (str): 요청 대상 URL.

        Returns:
            str: 렌더링 완료된 HTML 문자열.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("playwright 패키지가 설치되지 않았습니다.") from exc

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                html: str = page.content()
                browser.close()
                return html
        except Exception as exc:
            raise RuntimeError(f"Playwright 조회 실패: url={url}, reason={exc}") from exc

    def _download_binary(self, url: str) -> bytes:
        """
        URL에서 바이너리 콘텐츠를 다운로드한다.

        Args:
            url (str): 다운로드 대상 URL.

        Returns:
            bytes: 다운로드된 바이너리 데이터.
        """
        request = Request(
            url=url,
            headers={
                "User-Agent": self._user_agent,
                "Accept": "application/pdf,*/*",
            },
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"PDF 다운로드 실패: url={url}, reason={exc}") from exc

    def _parse_list_page(
        self,
        html: str,
        category: str,
        fallback_date: str,
    ) -> list[ReportSource]:
        """
        목록 페이지 HTML에서 리포트 항목들을 파싱한다.

        Args:
            html (str): 목록 페이지 HTML 문자열.
            category (str): 리포트 카테고리.
            fallback_date (str): 날짜 파싱 실패 시 대체 일자.

        Returns:
            list[ReportSource]: 파싱된 리포트 메타 목록.
        """
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table.type_1 tr")

        items: list[ReportSource] = []
        for row in rows:
            row_tag: Tag | None = row if isinstance(row, Tag) else None
            if row_tag is None:
                continue

            detail_anchor = row_tag.select_one("a[href*='_read.naver']")
            if not isinstance(detail_anchor, Tag):
                continue

            href: str = str(detail_anchor.get("href", "")).strip()
            title: str = detail_anchor.get_text(" ", strip=True)
            if not href or not title:
                continue

            detail_url: str = urljoin(self._BASE_URL, href)
            row_text: str = row_tag.get_text(" ", strip=True)
            date: str = self._extract_date(row_text, fallback=fallback_date)
            ticker: str = self._extract_ticker(row_tag)

            items.append(
                ReportSource(
                    title=title,
                    url=detail_url,
                    category=category,
                    date=date,
                    ticker=ticker,
                ),
            )

        return items

    def _extract_ticker(self, row: Tag) -> str:
        """
        목록 행에서 종목 코드를 추출한다.

        Args:
            row (Tag): 테이블 행 태그.

        Returns:
            str: 추출한 종목 코드, 없으면 MARKET.
        """
        stock_anchor = row.select_one("a[href*='code=']")
        if not isinstance(stock_anchor, Tag):
            return "MARKET"

        href: str = str(stock_anchor.get("href", "")).strip()
        parsed = urlparse(href)
        query_map: dict[str, list[str]] = parse_qs(parsed.query)
        code: str = query_map.get("code", [""])[0].strip().upper()
        return code if code else "MARKET"

    def _extract_date(self, text: str, fallback: str) -> str:
        """
        텍스트에서 날짜를 찾아 YYYYMMDD 형식으로 변환한다.

        Args:
            text (str): 원본 텍스트.
            fallback (str): 날짜를 찾지 못할 때 사용할 기본값.

        Returns:
            str: YYYYMMDD 형식 날짜 문자열.
        """
        match = re.search(r"(\d{4})[./-](\d{2})[./-](\d{2})", text)
        if not match:
            return fallback
        year, month, day = match.groups()
        return f"{year}{month}{day}"

    def _today_yyyymmdd(self) -> str:
        """
        오늘 날짜를 YYYYMMDD 형식으로 반환한다.

        Args:
            None

        Returns:
            str: YYYYMMDD 형식 날짜 문자열.
        """
        return datetime.now().strftime("%Y%m%d")


def fetch_report_sources(
    pages_per_category: int = 1,
    use_playwright: bool = False,
) -> list[ReportSource]:
    """
    네이버 리포트 목록 수집 함수(호환용 래퍼).

    Args:
        pages_per_category (int): 카테고리당 조회 페이지 수.
        use_playwright (bool): Playwright fallback 사용 여부.

    Returns:
        list[ReportSource]: 수집된 리포트 메타 목록.
    """
    collector = NaverReportCollector(use_playwright=use_playwright)
    return collector.fetch_report_sources(pages_per_category=pages_per_category)
