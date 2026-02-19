"""Claude 기반 리포트 요약 모듈."""

from __future__ import annotations

from typing import Any


class ClaudeReportSummarizer:
    """
    금융 리포트 요약 포맷을 생성하는 요약기.

    Args:
        api_key (str): Anthropic API 키.
        model (str): Claude 모델명.

    Returns:
        None: 요약기 객체를 생성한다.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._api_key: str = api_key
        self._model: str = model

    def summarize(self, report_text: str) -> str:
        """
        지정 포맷(의견/핵심포인트/리스크)으로 리포트를 요약한다.

        Args:
            report_text (str): 원문 리포트 텍스트.

        Returns:
            str: 마크다운 형식 요약 결과.
        """
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        prompt: str = (
            "다음 형식으로 금융 리포트를 요약하라. "
            "1) 투자의견/목표주가 2) 핵심 포인트(3줄) 3) 리스크 요인. "
            "수치 데이터는 원문 값을 변경하지 말고 그대로 인용하라.\n\n"
            f"원문:\n{report_text}"
        )

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic 패키지가 설치되지 않았습니다.") from exc

        client: Any = Anthropic(api_key=self._api_key)
        response: Any = client.messages.create(
            model=self._model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )

        return str(response.content[0].text)
