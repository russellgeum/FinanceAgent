"""벡터 검색 기반 RAG 응답 생성 모듈."""

from __future__ import annotations

from typing import Any


class RAGEngine:
    """
    ChromaDB 검색 결과를 기반으로 컨텍스트를 구성한다.

    Args:
        persist_directory (str): ChromaDB 저장 경로.
        collection_name (str): 검색할 컬렉션 이름.

    Returns:
        None: RAG 엔진 객체를 생성한다.
    """

    def __init__(self, persist_directory: str, collection_name: str) -> None:
        self._persist_directory: str = persist_directory
        self._collection_name: str = collection_name

    def _get_collection(self) -> Any:
        """
        ChromaDB 컬렉션 객체를 로드한다.

        Args:
            None

        Returns:
            Any: 검색 가능한 Chroma 컬렉션 객체.
        """
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb 패키지가 설치되지 않았습니다.") from exc

        client: Any = chromadb.PersistentClient(path=self._persist_directory)
        return client.get_or_create_collection(self._collection_name)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[str]:
        """
        질의 임베딩으로 상위 관련 청크를 조회한다.

        Args:
            query_embedding (list[float]): 질의 임베딩 벡터.
            top_k (int): 반환할 청크 수.

        Returns:
            list[str]: 관련 청크 텍스트 목록.
        """
        collection: Any = self._get_collection()
        result: Any = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        documents: list[list[str]] = result.get("documents", [[]])
        return documents[0] if documents else []
