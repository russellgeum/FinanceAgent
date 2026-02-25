"""환경 변수 기반 애플리케이션 설정 로더 모듈."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """
    PBT 런타임 환경 설정을 표현한다.

    Args:
        profile (str): 실행 프로파일 이름.
        anthropic_api_key (str): Claude API 키.
        claude_model (str): Claude 모델명.
        gemini_api_key (str): Gemini API 키.
        gemini_model (str): Gemini 모델명.
        voyage_api_key (str): Voyage API 키.
        voyage_model (str): Voyage 임베딩 모델명.
        kis_app_key (str): KIS API 키.
        run_ingestion_on_start (bool): 시작 시 수집 파이프라인 실행 여부.
        enable_vector_indexing (bool): 임베딩 및 벡터 저장 활성화 여부.
        naver_pages_per_category (int): 카테고리별 조회 페이지 수.
        naver_max_reports (int): 1회 실행 시 최대 처리 리포트 수.
        naver_use_playwright (bool): 정적 파싱 실패 시 Playwright fallback 사용 여부.

    Returns:
        None: 설정 데이터 모델 객체를 생성한다.
    """

    profile: str = Field(default="dev")
    anthropic_api_key: str = Field(default="")
    claude_model: str = Field(default="claude-sonnet-4-6")
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.0-flash")
    voyage_api_key: str = Field(default="")
    voyage_model: str = Field(default="voyage-finance-2")
    kis_app_key: str = Field(default="")
    run_ingestion_on_start: bool = Field(default=True)
    enable_vector_indexing: bool = Field(default=False)
    naver_pages_per_category: int = Field(default=1, ge=1)
    naver_max_reports: int = Field(default=10, ge=1)
    naver_use_playwright: bool = Field(default=False)


def _env_bool(name: str, default: bool) -> bool:
    """
    환경 변수 문자열을 bool 값으로 변환한다.

    Args:
        name (str): 환경 변수 키.
        default (bool): 값이 없을 때 사용할 기본값.

    Returns:
        bool: 파싱된 불리언 값.
    """
    value: str | None = os.getenv(name)
    if value is None:
        return default

    normalized: str = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _env_int(name: str, default: int) -> int:
    """
    환경 변수 문자열을 int 값으로 변환한다.

    Args:
        name (str): 환경 변수 키.
        default (int): 파싱 실패 시 기본값.

    Returns:
        int: 파싱된 정수 값.
    """
    value: str | None = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def load_app_config(project_root: Path) -> AppConfig:
    """
    .env 파일과 OS 환경 변수를 읽어 AppConfig를 생성한다.

    Args:
        project_root (Path): 프로젝트 루트 경로.

    Returns:
        AppConfig: 검증된 애플리케이션 설정 객체.
    """
    dotenv_path: Path = project_root / ".env"
    load_dotenv(dotenv_path)

    return AppConfig(
        profile=os.getenv("PBT_PROFILE", "dev"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        claude_model=os.getenv("PBT_CLAUDE_MODEL", "claude-sonnet-4-6"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("PBT_GEMINI_MODEL", "gemini-2.0-flash"),
        voyage_api_key=os.getenv("VOYAGE_API_KEY", ""),
        voyage_model=os.getenv("PBT_VOYAGE_MODEL", "voyage-finance-2"),
        kis_app_key=os.getenv("KIS_APP_KEY", ""),
        run_ingestion_on_start=_env_bool("PBT_RUN_INGESTION_ON_START", True),
        enable_vector_indexing=_env_bool("PBT_ENABLE_VECTOR_INDEXING", False),
        naver_pages_per_category=_env_int("PBT_NAVER_PAGES_PER_CATEGORY", 1),
        naver_max_reports=_env_int("PBT_NAVER_MAX_REPORTS", 10),
        naver_use_playwright=_env_bool("PBT_NAVER_USE_PLAYWRIGHT", False),
    )
