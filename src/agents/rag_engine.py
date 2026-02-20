"""벡터 검색 기반 RAG 응답 생성 모듈."""

from __future__ import annotations

from src.processors.embedder import BaseEmbedder
from src.storage.vector_store import BaseVectorStore


class RAGEngine:
    """
    추상화된 Embedder와 VectorStore를 주입받아 검색-생성 흐름을 제어한다.

    Args:
        embedder (BaseEmbedder): 임베딩 추상 인터페이스 구현체.
        vector_store (BaseVectorStore): 벡터 저장소 추상 인터페이스 구현체.

    Returns:
        None: RAG 엔진 객체를 생성한다.
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
    ) -> None:
        self._embedder: BaseEmbedder = embedder
        self._vector_store: BaseVectorStore = vector_store


    def search(self, query: str, top_k: int = 5) -> list[str]:
        """
        자연어 질의를 임베딩하여 유사 문서 청크를 검색한다.

        Args:
            query (str): 자연어 검색 질의.
            top_k (int): 반환할 청크 수.

        Returns:
            list[str]: 관련 청크 텍스트 목록.
        """
        query_embedding: list[float] = self._embedder.embed_query(query)
        return self._vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
        )
