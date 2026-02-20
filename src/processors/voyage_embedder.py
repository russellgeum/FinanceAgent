"""Voyage AI 임베딩 구현체 모듈."""

from __future__ import annotations

from typing import Any

from src.processors.embedder import BaseEmbedder


class VoyageEmbedder(BaseEmbedder):
    """
    Voyage AI API를 사용하는 텍스트 임베딩 구현체.

    Args:
        api_key (str): Voyage API 키.
        model (str): 임베딩 모델명.

    Returns:
        None: 임베딩 클라이언트 래퍼를 생성한다.
    """

    def __init__(self, api_key: str, model: str = "voyage-finance-2") -> None:
        self._api_key: str = api_key
        self._model: str = model


    def _get_client(self) -> Any:
        """
        Voyage AI 클라이언트를 생성한다.

        Args:
            None

        Returns:
            Any: voyageai.Client 인스턴스.
        """
        if not self._api_key:
            raise ValueError("VOYAGE_API_KEY가 설정되지 않았습니다.")

        try:
            import voyageai
        except ImportError as exc:
            raise RuntimeError(
                "voyageai 패키지가 설치되지 않았습니다.",
            ) from exc

        return voyageai.Client(api_key=self._api_key)


    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        입력 텍스트 목록을 벡터로 변환한다.

        Args:
            texts (list[str]): 임베딩할 문장 목록.

        Returns:
            list[list[float]]: 각 텍스트에 대응하는 임베딩 벡터.
        """
        client: Any = self._get_client()
        result: Any = client.embed(texts=texts, model=self._model)
        return [list(vector) for vector in result.embeddings]


    def embed_query(self, text: str) -> list[float]:
        """
        단일 질의 텍스트를 벡터로 변환한다.

        Args:
            text (str): 임베딩할 질의 텍스트.

        Returns:
            list[float]: 질의에 대한 임베딩 벡터.
        """
        results: list[list[float]] = self.embed_texts([text])
        return results[0]
