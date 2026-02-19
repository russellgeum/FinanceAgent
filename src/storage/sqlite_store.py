"""크롤링 이력 및 메타데이터 SQLite 저장 모듈."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class CrawlHistoryStore:
    """
    수집 이력 중복 체크를 위한 SQLite 저장소.

    Args:
        db_path (Path): SQLite 파일 경로.

    Returns:
        None: 저장소 객체를 생성한다.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path: Path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        """
        수집 이력 테이블을 생성한다.

        Args:
            None

        Returns:
            None: 스키마 초기화만 수행한다.
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crawl_history (
                    item_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """,
            )
            conn.commit()

    def exists(self, item_id: str) -> bool:
        """
        특정 항목이 이미 수집되었는지 확인한다.

        Args:
            item_id (str): 수집 항목 고유 ID.

        Returns:
            bool: 존재하면 True, 아니면 False.
        """
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT item_id FROM crawl_history WHERE item_id = ?",
                (item_id,),
            ).fetchone()
        return row is not None

    def insert(self, item_id: str, source_url: str, created_at: str) -> None:
        """
        신규 수집 항목 이력을 저장한다.

        Args:
            item_id (str): 수집 항목 고유 ID.
            source_url (str): 원본 URL.
            created_at (str): 생성 시각 문자열.

        Returns:
            None: 데이터 저장만 수행한다.
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO crawl_history(item_id, source_url, created_at)
                VALUES (?, ?, ?)
                """,
                (item_id, source_url, created_at),
            )
            conn.commit()
