"""리포트 메타데이터 및 문서 스키마 모듈."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ReportMetadata(BaseModel):
    """
    RAG 저장용 리포트 메타데이터 스키마.

    Args:
        ticker (str): 종목 코드 또는 MARKET.
        date (str): 문서 기준일(YYYYMMDD).
        category (str): 리포트 카테고리.
        url (str): 원본 URL.
        title (str): 문서 제목.

    Returns:
        None: 검증된 메타데이터 모델을 생성한다.
    """

    ticker: str = Field(min_length=1)
    date: str = Field(min_length=8, max_length=8)
    category: str = Field(min_length=1)
    url: str = Field(min_length=1)
    title: str = Field(min_length=1)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        """
        빈 종목 코드를 MARKET으로 정규화한다.

        Args:
            value (str): 입력 종목 코드.

        Returns:
            str: 정규화된 종목 코드.
        """
        normalized: str = value.strip().upper()
        return normalized if normalized else "MARKET"





class ReportDocument(BaseModel):
    """
    텍스트와 메타데이터를 함께 관리하는 문서 스키마.

    Args:
        content (str): 리포트 본문 텍스트.
        metadata (ReportMetadata): 문서 메타데이터.

    Returns:
        None: 검증된 문서 모델을 생성한다.
    """

    content: str = Field(min_length=1)
    metadata: ReportMetadata
