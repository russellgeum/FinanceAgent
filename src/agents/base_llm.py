"""LLM 추론 엔진 추상 인터페이스 모듈."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMEngine(ABC):
    """
    다양한 LLM 제공자를 통합 관리하는 추상 인터페이스.

    Args:
        None

    Returns:
        None: 추상 LLM 엔진 인터페이스를 정의한다.
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs: object) -> str:
        """
        프롬프트를 기반으로 텍스트를 생성한다.

        Args:
            prompt (str): LLM에 전달할 프롬프트.
            **kwargs: 추가 생성 옵션.

        Returns:
            str: 생성된 텍스트 응답.
        """
