"""개인용 블룸버그 터미널(PBT)의 실행 엔트리 포인트."""

from __future__ import annotations

from pathlib import Path

from src.agents.ingestion_pipeline import NaverRAGIngestionPipeline
from src.utils.config import AppConfig, load_app_config
from src.utils.datetime_utils import now_stamp
from src.utils.logging_utils import get_daily_logger


def bootstrap_directories(project_root: Path) -> None:
    """
    프로젝트 필수 디렉터리를 초기화한다.

    Args:
        project_root (Path): 프로젝트 루트 경로.

    Returns:
        None: 디렉터리 생성 작업만 수행한다.
    """
    required_dirs: list[Path] = [
        project_root / "data" / "report",
        project_root / "data" / "stock",
        project_root / "data" / "system",
        project_root / "data" / "chroma",
        project_root / "response" / "report",
        project_root / "logs",
    ]
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)


def run_ingestion(project_root: Path, config: AppConfig) -> None:
    """
    네이버 리포트 수집, RAG 적재, Claude 요약 파이프라인을 실행한다.

    Args:
        project_root (Path): 프로젝트 루트 경로.
        config (AppConfig): 애플리케이션 설정.

    Returns:
        None: 파이프라인 수행 결과를 로깅한다.
    """
    logger = get_daily_logger(project_root)

    if not config.run_ingestion_on_start:
        logger.info("시작 시 수집 파이프라인 실행이 비활성화되어 있습니다.")
        return

    pipeline = NaverRAGIngestionPipeline(
        project_root=project_root,
        voyage_api_key=config.voyage_api_key,
        anthropic_api_key=config.anthropic_api_key,
        pages_per_category=config.naver_pages_per_category,
        max_reports=config.naver_max_reports,
        use_playwright=config.naver_use_playwright,
        logger=logger,
    )
    summary = pipeline.run()
    logger.info("파이프라인 실행 완료: %s", summary.to_dict())


def run() -> None:
    """
    애플리케이션 기본 초기화와 시작 파이프라인을 수행한다.

    Args:
        None

    Returns:
        None: 실행 상태를 로거에 기록한다.
    """
    project_root: Path = Path(__file__).resolve().parent
    config: AppConfig = load_app_config(project_root)
    bootstrap_directories(project_root)

    logger = get_daily_logger(project_root)
    logger.info("PBT 시작: profile=%s, timestamp=%s", config.profile, now_stamp())

    try:
        run_ingestion(project_root=project_root, config=config)
    except Exception as exc:
        logger.exception("파이프라인 실행 실패: reason=%s", exc)


if __name__ == "__main__":
    run()
