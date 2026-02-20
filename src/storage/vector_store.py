"""벡터 저장소 추상 인터페이스 모듈."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.processors.schemas import ReportMetadata


class BaseVectorStore(ABC):
    """
    벡터 검색 및 저장을 담당하는 추상 인터페이스.

    Args:
        None

    Returns:
        None: 추상 벡터 저장소 인터페이스를 정의한다.
    """

    @abstractmethod
    def make_document_id(self, metadata: ReportMetadata) -> str:
        """
        메타데이터 기준의 고유 문서 ID를 생성한다.

        Args:
            metadata (ReportMetadata): 리포트 메타데이터.

        Returns:
            str: {date}_{ticker}_{title_hash} 형식의 고유 ID.
        """


    @abstractmethod
    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, str]],
    ) -> None:
        """
        문서 청크와 임베딩을 저장소에 추가한다.

        Args:
            ids (list[str]): 문서 고유 ID 목록.
            documents (list[str]): 청크 텍스트 목록.
            embeddings (list[list[float]]): 임베딩 벡터 목록.
            metadatas (list[dict[str, str]]): 메타데이터 목록.

        Returns:
            None: 벡터 데이터를 저장한다.
        """


    @abstractmethod
    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[str]:
        """
        질의 임베딩으로 유사한 문서 청크를 검색한다.

        Args:
            query_embedding (list[float]): 질의 임베딩 벡터.
            top_k (int): 반환할 청크 수.

        Returns:
            list[str]: 유사도 상위 청크 텍스트 목록.
        """
