"""Gemini 기반 리포트 요약 모듈."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GeminiReportSummarizer:
    """
    Gemini API를 이용해 금융 리포트 요약을 생성한다.

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
        self._api_key: str = api_key
        self._model: str = model
        self._timeout_seconds: int = timeout_seconds
        self._max_retries: int = max_retries
        self._retry_backoff_seconds: float = retry_backoff_seconds

    def summarize(self, report_text: str) -> str:
        """
        지정 포맷(의견/핵심포인트/리스크)으로 리포트를 요약한다.

        Args:
            report_text (str): 원문 리포트 텍스트.

        Returns:
            str: 마크다운 형식 요약 결과.
        """
        if not self._api_key.strip():
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

        prompt: str = (
            "다음 형식으로 금융 리포트를 요약하라. "
            "1) 투자의견/목표주가 2) 핵심 포인트(3줄) 3) 리스크 요인. "
            "수치 데이터는 원문 값을 변경하지 말고 그대로 인용하라.\n\n"
            f"원문:\n{report_text}"
        )
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1200,
            },
        }
        endpoint: str = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={quote(self._api_key, safe='')}"
        )
        request = Request(
            url=endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        body: bytes = self._request_with_retry(request)

        try:
            data: dict[str, Any] = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini API 응답 JSON 파싱 실패") from exc

        candidates: list[dict[str, Any]] = list(data.get("candidates", []))
        if not candidates:
            raise RuntimeError("Gemini API 응답에 candidates가 없습니다.")

        content: dict[str, Any] = dict(candidates[0].get("content", {}))
        parts: list[dict[str, Any]] = list(content.get("parts", []))
        texts: list[str] = []
        part: dict[str, Any]
        for part in parts:
            piece: str = str(part.get("text", "")).strip()
            if piece:
                texts.append(piece)

        merged_text: str = "\n".join(texts).strip()
        if not merged_text:
            raise RuntimeError("Gemini API 응답 텍스트가 비어 있습니다.")

        return merged_text

    def _request_with_retry(self, request: Request) -> bytes:
        """
        Gemini API 요청을 수행하고 재시도 가능한 오류는 백오프로 재시도한다.

        Args:
            request (Request): URL 요청 객체.

        Returns:
            bytes: 성공 응답 본문.
        """
        retryable_status_codes: set[int] = {429, 500, 502, 503, 504}

        attempt: int
        for attempt in range(self._max_retries + 1):
            try:
                with urlopen(request, timeout=self._timeout_seconds) as response:
                    return response.read()
            except HTTPError as exc:
                detail: str = exc.read().decode("utf-8", errors="ignore")
                is_retryable: bool = exc.code in retryable_status_codes
                if is_retryable and attempt < self._max_retries:
                    sleep_seconds: float = self._retry_backoff_seconds * (attempt + 1)
                    time.sleep(sleep_seconds)
                    continue
                raise RuntimeError(
                    f"Gemini API 호출 실패: status={exc.code}, reason={detail}",
                ) from exc
            except (URLError, TimeoutError) as exc:
                if attempt < self._max_retries:
                    sleep_seconds = self._retry_backoff_seconds * (attempt + 1)
                    time.sleep(sleep_seconds)
                    continue
                raise RuntimeError(f"Gemini API 네트워크 오류: reason={exc}") from exc

        raise RuntimeError("Gemini API 재시도 한도를 초과했습니다.")
