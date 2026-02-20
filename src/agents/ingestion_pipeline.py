"""네이버 리포트 수집 및 RAG 적재 파이프라인 모듈."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from src.agents.gemini_summarizer import GeminiReportSummarizer
from src.agents.summarizer import ClaudeReportSummarizer
from src.collectors.naver_report_collector import NaverReportCollector, ReportSource
from src.processors.chunker import chunk_text
from src.processors.embedder import VoyageEmbedder
from src.processors.pdf_parser import extract_text_from_pdf
from src.processors.schemas import ReportMetadata
from src.storage.sqlite_store import CrawlHistoryStore
from src.storage.vector_store import ChromaReportStore
from src.utils.datetime_utils import now_stamp


@dataclass(slots=True)
class IngestionSummary:
    """
    파이프라인 실행 결과 요약 정보를 담는다.

    Args:
        started_at (str): 실행 시작 타임스탬프(YYYYMMDDHHMM).
        collected_count (int): 목록에서 수집한 항목 수.
        processed_count (int): 성공적으로 벡터 저장한 항목 수.
        skipped_duplicate_count (int): 중복으로 건너뛴 항목 수.
        skipped_error_count (int): 오류로 실패한 항목 수.
        report_batch_dir (str): PDF 저장 디렉터리 경로.
        response_batch_dir (str): 요약 결과 저장 디렉터리 경로.

    Returns:
        None: 실행 결과 데이터 객체를 생성한다.
    """

    started_at: str
    collected_count: int
    processed_count: int
    skipped_duplicate_count: int
    skipped_error_count: int
    report_batch_dir: str
    response_batch_dir: str

    def to_dict(self) -> dict[str, str | int]:
        """
        요약 객체를 JSON 직렬화 가능한 딕셔너리로 변환한다.

        Args:
            None

        Returns:
            dict[str, str | int]: 실행 결과 딕셔너리.
        """
        return asdict(self)




class NaverRAGIngestionPipeline:
    """
    네이버 리포트를 수집해 벡터 DB 적재와 통합 요약을 수행한다.

    Args:
        project_root (Path): 프로젝트 루트 경로.
        voyage_api_key (str): Voyage API 키.
        voyage_model (str): Voyage 임베딩 모델명.
        anthropic_api_key (str): Anthropic API 키.
        claude_model (str): Claude 모델명.
        gemini_api_key (str): Gemini API 키.
        gemini_model (str): Gemini 모델명.
        pages_per_category (int): 카테고리당 조회 페이지 수.
        max_reports (int): 최대 처리 리포트 수.
        use_playwright (bool): 크롤링 시 Playwright fallback 사용 여부.
        logger (logging.Logger): 로깅 객체.

    Returns:
        None: 파이프라인 객체를 생성한다.
    """

    def __init__(
        self,
        project_root: Path,
        voyage_api_key: str,
        voyage_model: str,
        anthropic_api_key: str,
        claude_model: str,
        gemini_api_key: str,
        gemini_model: str,
        pages_per_category: int,
        max_reports: int,
        use_playwright: bool,
        logger: logging.Logger,
    ) -> None:
        self._project_root: Path = project_root
        self._voyage_api_key: str = voyage_api_key
        self._voyage_model: str = voyage_model
        self._anthropic_api_key: str = anthropic_api_key
        self._claude_model: str = claude_model
        self._gemini_api_key: str = gemini_api_key
        self._gemini_model: str = gemini_model
        self._pages_per_category: int = pages_per_category
        self._max_reports: int = max_reports
        self._logger: logging.Logger = logger

        self._collector = NaverReportCollector(use_playwright=use_playwright)
        self._embedder = VoyageEmbedder(
            api_key=voyage_api_key,
            model=voyage_model,
        )
        self._claude_summarizer = ClaudeReportSummarizer(
            api_key=anthropic_api_key,
            model=claude_model,
        )
        self._gemini_summarizer = GeminiReportSummarizer(
            api_key=gemini_api_key,
            model=gemini_model,
        )
        self._vector_store = ChromaReportStore(
            persist_directory=self._project_root / "data" / "chroma",
        )
        self._history_store = CrawlHistoryStore(
            db_path=self._project_root / "data" / "system" / "crawl_history.db",
        )

    def run(self) -> IngestionSummary:
        """
        수집부터 Chroma 적재 및 통합 요약까지 전체 파이프라인을 실행한다.

        Args:
            None

        Returns:
            IngestionSummary: 실행 요약 정보.
        """
        if not self._voyage_api_key.strip():
            raise ValueError(
                "VOYAGE_API_KEY가 비어 있어 임베딩/벡터 적재를 진행할 수 없습니다.",
            )
        if not self._anthropic_api_key.strip() and not self._gemini_api_key.strip():
            raise ValueError(
                "ANTHROPIC_API_KEY 또는 GEMINI_API_KEY 중 하나는 필요합니다.",
            )

        started_at: str = now_stamp()
        report_batch_dir: Path = self._project_root / "data" / "report" / started_at
        response_batch_dir: Path = (
            self._project_root / "response" / "report" / started_at
        )
        report_batch_dir.mkdir(parents=True, exist_ok=True)
        response_batch_dir.mkdir(parents=True, exist_ok=True)

        self._logger.info(
            "리포트 수집 시작: pages_per_category=%s, max_reports=%s",
            self._pages_per_category,
            self._max_reports,
        )

        sources: list[ReportSource] = self._collector.fetch_report_sources(
            pages_per_category=self._pages_per_category,
        )
        fetch_errors: list[str] = self._collector.get_last_fetch_errors()
        if not sources and fetch_errors:
            sampled_errors: str = " | ".join(fetch_errors[:3])
            raise RuntimeError(
                "리포트 수집 결과가 0건이며 목록 조회 에러가 존재합니다. "
                f"details={sampled_errors}",
            )
        if not sources:
            self._logger.warning(
                "리포트 수집 결과가 0건입니다. "
                "목록 구조 변경 또는 일시적 게시물 부재 여부를 확인하세요.",
            )
        limited_sources: list[ReportSource] = sources[: self._max_reports]

        processed_count: int = 0
        skipped_duplicate_count: int = 0
        skipped_error_count: int = 0

        for source in limited_sources:
            metadata = ReportMetadata(
                ticker=source.ticker,
                date=source.date,
                category=source.category,
                url=source.url,
                title=source.title,
            )
            document_id: str = self._vector_store.make_document_id(metadata)

            if self._history_store.exists(document_id):
                skipped_duplicate_count += 1
                self._logger.info("중복 항목 스킵: id=%s, title=%s", document_id, source.title)
                continue

            try:
                pdf_url: str | None = self._collector.resolve_pdf_url(source.url)
                if not pdf_url:
                    raise RuntimeError("상세 페이지에서 PDF URL을 찾지 못했습니다.")

                pdf_path: Path = report_batch_dir / f"{document_id}.pdf"
                self._collector.download_pdf(pdf_url, pdf_path)

                content: str = extract_text_from_pdf(pdf_path)
                chunks: list[str] = chunk_text(content)
                if not chunks:
                    raise RuntimeError("PDF 텍스트 청킹 결과가 비어 있습니다.")

                embeddings: list[list[float]] = self._embedder.embed_texts(chunks)
                chunk_ids: list[str] = [
                    f"{document_id}_{index:04d}"
                    for index in range(1, len(chunks) + 1)
                ]
                chunk_metadatas: list[dict[str, str]] = []
                for index in range(1, len(chunks) + 1):
                    chunk_metadatas.append(
                        {
                            "ticker": metadata.ticker,
                            "date": metadata.date,
                            "category": metadata.category,
                            "url": metadata.url,
                            "title": metadata.title,
                            "document_id": document_id,
                            "chunk_index": str(index),
                        },
                    )

                self._vector_store.upsert(
                    ids=chunk_ids,
                    documents=chunks,
                    embeddings=embeddings,
                    metadatas=chunk_metadatas,
                )
                claude_summary, claude_error = self._try_provider_summary(
                    provider_name="Claude",
                    summarize_func=self._claude_summarizer.summarize,
                    report_text=content,
                )
                gemini_summary, gemini_error = self._try_provider_summary(
                    provider_name="Gemini",
                    summarize_func=self._gemini_summarizer.summarize,
                    report_text=content,
                )

                if claude_summary is None and gemini_summary is None:
                    raise RuntimeError(
                        "Claude/Gemini 요약이 모두 실패했습니다. "
                        f"claude={claude_error}, gemini={gemini_error}",
                    )

                if claude_summary is None and gemini_summary is not None:
                    self._logger.warning(
                        "Claude 요약 실패, Gemini 폴백 사용: id=%s, reason=%s",
                        document_id,
                        claude_error,
                    )
                if gemini_summary is None and claude_summary is not None:
                    self._logger.warning(
                        "Gemini 요약 실패, Claude 폴백 사용: id=%s, reason=%s",
                        document_id,
                        gemini_error,
                    )

                summary_markdown: str = self._merge_summaries(
                    claude_summary=claude_summary,
                    gemini_summary=gemini_summary,
                    claude_error=claude_error,
                    gemini_error=gemini_error,
                )
                self._write_report_summary(
                    document_id=document_id,
                    summary_text=summary_markdown,
                    directory=response_batch_dir,
                )
                self._history_store.insert(
                    item_id=document_id,
                    source_url=source.url,
                    created_at=datetime.now().isoformat(timespec="seconds"),
                )
                processed_count += 1
                self._logger.info(
                    "적재/통합요약 성공: id=%s, title=%s, chunks=%s",
                    document_id,
                    source.title,
                    len(chunks),
                )
            except Exception as exc:
                skipped_error_count += 1
                self._logger.exception(
                    "리포트 처리 실패: title=%s, url=%s, reason=%s",
                    source.title,
                    source.url,
                    exc,
                )

        summary = IngestionSummary(
            started_at=started_at,
            collected_count=len(limited_sources),
            processed_count=processed_count,
            skipped_duplicate_count=skipped_duplicate_count,
            skipped_error_count=skipped_error_count,
            report_batch_dir=str(report_batch_dir),
            response_batch_dir=str(response_batch_dir),
        )
        self._write_summary(summary, response_batch_dir)
        self._logger.info("리포트 수집 종료: %s", summary.to_dict())

        return summary

    def _try_provider_summary(
        self,
        provider_name: str,
        summarize_func: Callable[[str], str],
        report_text: str,
    ) -> tuple[str | None, str | None]:
        """
        단일 요약 제공자 호출을 시도하고 성공/실패 결과를 반환한다.

        Args:
            provider_name (str): 제공자 이름(Claude/Gemini).
            summarize_func (Callable[[str], str]): 요약 함수.
            report_text (str): 요약 대상 원문 텍스트.

        Returns:
            tuple[str | None, str | None]:
                성공 시 (요약문, None), 실패 시 (None, 에러 요약문).
        """
        try:
            summary: str = summarize_func(report_text)
            return summary, None
        except Exception as exc:
            error_message: str = self._format_error_message(exc)
            self._logger.warning(
                "%s 요약 실패: reason=%s",
                provider_name,
                error_message,
            )
            return None, error_message

    def _format_error_message(self, exc: Exception) -> str:
        """
        예외 메시지를 로그/요약용 한 줄 문자열로 정리한다.

        Args:
            exc (Exception): 발생 예외 객체.

        Returns:
            str: 줄바꿈 제거 및 길이 제한을 적용한 에러 문자열.
        """
        normalized: str = " ".join(str(exc).split())
        if len(normalized) <= 220:
            return normalized
        return f"{normalized[:217]}..."

    def _merge_summaries(
        self,
        claude_summary: str | None,
        gemini_summary: str | None,
        claude_error: str | None,
        gemini_error: str | None,
    ) -> str:
        """
        Claude/Gemini 요약 결과를 단일 마크다운으로 병합한다.

        Args:
            claude_summary (str | None): Claude 요약 결과.
            gemini_summary (str | None): Gemini 요약 결과.
            claude_error (str | None): Claude 실패 원인.
            gemini_error (str | None): Gemini 실패 원인.

        Returns:
            str: 병합된 단일 마크다운 텍스트.
        """
        claude_section: str
        gemini_section: str
        if claude_summary is not None:
            claude_section = claude_summary.strip()
        else:
            claude_section = (
                "요약 생성 실패. "
                f"실패 원인: {claude_error or '알 수 없는 오류'}"
            )

        if gemini_summary is not None:
            gemini_section = gemini_summary.strip()
        else:
            gemini_section = (
                "요약 생성 실패. "
                f"실패 원인: {gemini_error or '알 수 없는 오류'}"
            )

        return (
            "# 통합 리포트 요약\n\n"
            "## Claude 요약\n\n"
            f"{claude_section}\n\n"
            "## Gemini 요약\n\n"
            f"{gemini_section}\n"
        )

    def _write_report_summary(
        self,
        document_id: str,
        summary_text: str,
        directory: Path,
    ) -> Path:
        """
        개별 리포트 요약 결과를 마크다운 파일로 저장한다.

        Args:
            document_id (str): 리포트 고유 문서 ID.
            summary_text (str): 통합 요약 결과 텍스트.
            directory (Path): 저장 디렉터리.

        Returns:
            Path: 저장된 요약 파일 경로.
        """
        summary_path: Path = directory / f"{document_id}.md"
        summary_path.write_text(summary_text, encoding="utf-8")
        return summary_path

    def _write_summary(self, summary: IngestionSummary, directory: Path) -> None:
        """
        실행 요약을 JSON 파일로 저장한다.

        Args:
            summary (IngestionSummary): 실행 결과 요약.
            directory (Path): 저장 디렉터리.

        Returns:
            None: 파일 저장만 수행한다.
        """
        summary_path: Path = directory / "ingestion_summary.json"
        summary_path.write_text(
            json.dumps(summary.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
