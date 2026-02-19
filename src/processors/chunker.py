"""금융 리포트 텍스트 청킹 모듈."""

from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """
    긴 텍스트를 고정 길이 기반 청크 리스트로 분할한다.

    Args:
        text (str): 분할할 원문 텍스트.
        chunk_size (int): 청크 최대 길이.
        overlap (int): 다음 청크와 겹칠 길이.

    Returns:
        list[str]: 청크 문자열 목록.
    """
    cleaned: str = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[str] = []
    step: int = max(1, chunk_size - overlap)
    for idx in range(0, len(cleaned), step):
        part: str = cleaned[idx: idx + chunk_size]
        if part:
            chunks.append(part)
    return chunks
