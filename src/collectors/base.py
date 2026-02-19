"""시장 데이터 수집기 추상화 모듈."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class MarketDataCollector(ABC):
    """
    주가 데이터 공급자 교체를 위한 수집기 인터페이스.

    Args:
        None

    Returns:
        None: 인터페이스 정의용 추상 클래스다.
    """

    @abstractmethod
    def fetch_ohlcv(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        특정 종목의 OHLCV 시계열 데이터를 조회한다.

        Args:
            ticker (str): 종목 코드.
            start_date (str): 시작일(YYYY-MM-DD).
            end_date (str): 종료일(YYYY-MM-DD).

        Returns:
            pd.DataFrame: DatetimeIndex 기반 시계열 데이터.
        """
        raise NotImplementedError
