"""Gemini 기반 리포트 요약 모듈 (하위 호환성 유지용)."""

from __future__ import annotations

from src.agents.gemini_engine import GeminiEngine
from src.agents.summarizer import ReportSummarizer


class GeminiReportSummarizer:
    """
    Gemini API를 이용해 금융 리포트 요약을 생성한다.

    GeminiEngine + ReportSummarizer 조합으로 위임하여 동작한다.

    Args:
        api_key (str): Gemini API 키.
        model (str): Gemini 모델명.
        timeout_seconds (int): API 요청 타임아웃(초).
        max_retries (int): 재시도 횟수(최초 요청 제외).
        retry_backoff_seconds (float): 재시도 백오프 기준(초).

    Returns:
        None: 요약기 객체를 생성한다.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        timeout_seconds: int = 60,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.5,
    ) -> None:
        engine = GeminiEngine(
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )
        self._summarizer = ReportSummarizer(engine=engine)


    def summarize(self, report_text: str) -> str:
        """
        지정 포맷(의견/핵심포인트/리스크)으로 리포트를 요약한다.

        Args:
            report_text (str): 원문 리포트 텍스트.

        Returns:
            str: 마크다운 형식 요약 결과.
        """
        return self._summarizer.summarize(report_text)
