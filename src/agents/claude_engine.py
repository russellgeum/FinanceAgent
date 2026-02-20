"""Claude LLM 추론 엔진 구현체 모듈."""

from __future__ import annotations

from typing import Any

from src.agents.base_llm import BaseLLMEngine


class ClaudeEngine(BaseLLMEngine):
    """
    Anthropic Claude API를 사용하는 LLM 추론 엔진.

    Args:
        api_key (str): Anthropic API 키.
        model (str): Claude 모델명.

    Returns:
        None: Claude 엔진 객체를 생성한다.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._api_key: str = api_key
        self._model: str = model


    def generate(self, prompt: str, **kwargs: object) -> str:
        """
        Claude API를 호출하여 텍스트를 생성한다.

        Args:
            prompt (str): LLM에 전달할 프롬프트.
            **kwargs: 추가 생성 옵션(max_tokens 등).

        Returns:
            str: 생성된 텍스트 응답.
        """
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic 패키지가 설치되지 않았습니다.") from exc

        max_tokens: int = int(kwargs.get("max_tokens", 1200))

        client: Any = Anthropic(api_key=self._api_key)
        response: Any = client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        return str(response.content[0].text)
