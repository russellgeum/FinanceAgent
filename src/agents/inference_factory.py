"""LLM 추론 엔진 팩토리 모듈."""

from __future__ import annotations

from src.agents.base_llm import BaseLLMEngine
from src.agents.claude_engine import ClaudeEngine
from src.agents.gemini_engine import GeminiEngine


def create_llm_engine(
    provider: str,
    api_key: str,
    model: str,
    **kwargs: object,
) -> BaseLLMEngine:
    """
    설정에 따라 적절한 LLM 추론 엔진 구현체를 반환한다.

    Args:
        provider (str): LLM 제공자 이름("claude" 또는 "gemini").
        api_key (str): API 키.
        model (str): 모델명.
        **kwargs: 엔진별 추가 설정(timeout_seconds, max_retries 등).

    Returns:
        BaseLLMEngine: 생성된 LLM 엔진 인스턴스.

    Raises:
        ValueError: 지원되지 않는 provider가 전달된 경우.
    """
    normalized: str = provider.strip().lower()

    if normalized == "claude":
        return ClaudeEngine(api_key=api_key, model=model)

    if normalized == "gemini":
        return GeminiEngine(
            api_key=api_key,
            model=model,
            timeout_seconds=int(kwargs.get("timeout_seconds", 60)),
            max_retries=int(kwargs.get("max_retries", 3)),
            retry_backoff_seconds=float(
                kwargs.get("retry_backoff_seconds", 1.5),
            ),
        )

    raise ValueError(f"지원되지 않는 LLM provider입니다: {provider}")
