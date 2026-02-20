"""LLM 기반 리포트 요약 모듈."""

from __future__ import annotations

from src.agents.base_llm import BaseLLMEngine


class ReportSummarizer:
    """
    BaseLLMEngine을 주입받아 금융 리포트 요약을 생성하는 요약기.

    Args:
        engine (BaseLLMEngine): LLM 추론 엔진 인스턴스.

    Returns:
        None: 요약기 객체를 생성한다.
    """

    def __init__(self, engine: BaseLLMEngine) -> None:
        self._engine: BaseLLMEngine = engine


    def summarize(self, report_text: str) -> str:
        """
        지정 포맷(의견/핵심포인트/리스크)으로 리포트를 요약한다.

        Args:
            report_text (str): 원문 리포트 텍스트.

        Returns:
            str: 마크다운 형식 요약 결과.
        """
        prompt: str = (
            "다음 형식으로 금융 리포트를 요약하라. "
            "1) 투자의견/목표주가 2) 핵심 포인트(3줄) 3) 리스크 요인. "
            "수치 데이터는 원문 값을 변경하지 말고 그대로 인용하라.\n\n"
            f"원문:\n{report_text}"
        )

        return self._engine.generate(prompt)
