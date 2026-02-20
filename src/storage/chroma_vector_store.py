"""ChromaDB 벡터 저장소 구현체 모듈."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.processors.schemas import ReportMetadata
from src.storage.vector_store import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    """
    ChromaDB를 사용하는 벡터 저장소 구현체.

    Args:
        persist_directory (Path): ChromaDB 영속화 경로.
        collection_name (str): 컬렉션 이름.

    Returns:
        None: 벡터 저장소 객체를 생성한다.
    """

    def __init__(
        self,
        persist_directory: Path,
        collection_name: str = "report_chunks",
    ) -> None:
        self._persist_directory: Path = persist_directory
        self._collection_name: str = collection_name
        self._persist_directory.mkdir(parents=True, exist_ok=True)


    def _build_client(self) -> Any:
        """
        ChromaDB 클라이언트 인스턴스를 생성한다.

        Args:
            None

        Returns:
            Any: ChromaDB persistent client 객체.
        """
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb 패키지가 설치되지 않았습니다.") from exc

        return chromadb.PersistentClient(path=str(self._persist_directory))


    def _get_collection(self) -> Any:
        """
        ChromaDB 컬렉션 객체를 로드한다.

        Args:
            None

        Returns:
            Any: 검색 가능한 Chroma 컬렉션 객체.
        """
        client: Any = self._build_client()
        return client.get_or_create_collection(self._collection_name)


    def make_document_id(self, metadata: ReportMetadata) -> str:
        """
        메타데이터 기준의 고유 문서 ID를 생성한다.

        Args:
            metadata (ReportMetadata): 리포트 메타데이터.

        Returns:
            str: {date}_{ticker}_{title_hash} 형식의 고유 ID.
        """
        title_hash: str = hashlib.sha1(
            metadata.title.encode("utf-8"),
        ).hexdigest()[:12]
        return f"{metadata.date}_{metadata.ticker}_{title_hash}"


    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, str]],
    ) -> None:
        """
        문서 청크와 임베딩을 컬렉션에 저장한다.

        Args:
            ids (list[str]): 문서 고유 ID 목록.
            documents (list[str]): 청크 텍스트 목록.
            embeddings (list[list[float]]): 임베딩 벡터 목록.
            metadatas (list[dict[str, str]]): 메타데이터 목록.

        Returns:
            None: 벡터 데이터를 영속화한다.
        """
        collection: Any = self._get_collection()
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )


    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[str]:
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
