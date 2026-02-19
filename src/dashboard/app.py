"""PBT 기본 대시보드 화면 모듈."""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import streamlit as st


def run_dashboard() -> None:
    """
    투자 보조 대시보드의 기본 레이아웃을 렌더링한다.

    Args:
        None

    Returns:
        None: Streamlit UI를 출력한다.
    """
    st.set_page_config(page_title="PBT Dashboard", layout="wide")
    st.title("개인용 블룸버그 터미널 (PBT)")
    st.caption("리포트 RAG 분석 및 투자 의사결정 지원")

    left, right = st.columns(2)
    with left:
        st.subheader("요약 결과")
        st.info("아직 분석 결과가 없습니다. 데이터 수집 후 표시됩니다.")
    with right:
        st.subheader("시장 상태")
        st.metric(label="KOSPI", value="-", delta="-")


if __name__ == "__main__":
    run_dashboard()
