"""파일/콘솔 로깅 초기화 모듈."""

from __future__ import annotations

import logging
from pathlib import Path

from src.utils.datetime_utils import today_log_name


def get_daily_logger(project_root: Path) -> logging.Logger:
    """
    일자별 로그 파일을 사용하는 로거를 생성한다.

    Args:
        project_root (Path): 프로젝트 루트 경로.

    Returns:
        logging.Logger: 파일과 콘솔 핸들러가 연결된 로거.
    """
    logger: logging.Logger = logging.getLogger("pbt")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_dir: Path = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path: Path = log_dir / f"{today_log_name()}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
