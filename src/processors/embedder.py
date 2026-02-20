"""임베딩 추상 인터페이스 모듈."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """
    텍스트를 벡터로 변환하는 임베딩 추상 인터페이스.

    Args:
        None

    Returns:
        None: 추상 임베더 인터페이스를 정의한다.
    """

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        입력 텍스트 목록을 벡터로 변환한다.

        Args:
            texts (list[str]): 임베딩할 문장 목록.

        Returns:
            list[list[float]]: 각 텍스트에 대응하는 임베딩 벡터.
        """


    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """
        단일 질의 텍스트를 벡터로 변환한다.

        Args:
            text (str): 임베딩할 질의 텍스트.

        Returns:
            list[float]: 질의에 대한 임베딩 벡터.
        """
