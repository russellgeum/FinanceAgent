"""FinanceDataReader 기반 주가 수집기 모듈."""

from __future__ import annotations

import pandas as pd

from src.collectors.base import MarketDataCollector


class FinanceDataReaderCollector(MarketDataCollector):
    """
    FinanceDataReader를 사용해 주가 데이터를 조회한다.

    Args:
        None

    Returns:
        None: 수집기 객체를 생성한다.
    """

    def fetch_ohlcv(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        종목의 기간별 OHLCV 데이터를 DataFrame으로 반환한다.

        Args:
            ticker (str): 종목 코드.
            start_date (str): 시작일(YYYY-MM-DD).
            end_date (str): 종료일(YYYY-MM-DD).

        Returns:
            pd.DataFrame: DatetimeIndex를 가진 시계열 데이터.
        """
        try:
            import FinanceDataReader as fdr
        except ImportError as exc:
            raise RuntimeError(
                "FinanceDataReader가 설치되지 않았습니다. "
                "requirements.txt를 설치하세요.",
            ) from exc

        frame: pd.DataFrame = fdr.DataReader(ticker, start_date, end_date)
        frame.index = pd.to_datetime(frame.index)
        return frame.sort_index()
