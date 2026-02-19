"""날짜/시간 포맷 유틸리티 모듈."""

from __future__ import annotations

from datetime import datetime


def now_stamp() -> str:
    """
    현재 시각을 파일/폴더 저장용 타임스탬프 문자열로 반환한다.

    Args:
        None

    Returns:
        str: YYYYMMDDHHMM 형식의 문자열.
    """
    return datetime.now().strftime("%Y%m%d%H%M")


def today_log_name() -> str:
    """
    로그 파일명에 사용하는 오늘 날짜 문자열을 반환한다.

    Args:
        None

    Returns:
        str: YYYYMMDD 형식의 문자열.
    """
    return datetime.now().strftime("%Y%m%d")
