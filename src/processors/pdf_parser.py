"""금융 리포트 PDF 텍스트 추출 모듈."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Callable


_HANGUL_PATTERN = re.compile(r"[가-힣]")
_ALNUM_PATTERN = re.compile(r"[A-Za-z0-9가-힣]")
_DIGIT_PATTERN = re.compile(r"\d")


@dataclass(slots=True)
class ParserCandidateStats:
    """
    단일 PDF 파서의 추출 품질 통계를 표현한다.

    Args:
        parser_name (str): 파서 이름.
        text_length (int): 정규화 텍스트 길이.
        hangul_count (int): 한글 문자 수.
        hangul_ratio (float): 의미 문자 대비 한글 비율.
        digit_ratio (float): 의미 문자 대비 숫자 비율.
        token_count (int): 공백 기준 토큰 수.
        quality_score (float): 최종 품질 점수.

    Returns:
        None: 파서 품질 통계 객체를 생성한다.
    """

    parser_name: str
    text_length: int
    hangul_count: int
    hangul_ratio: float
    digit_ratio: float
    token_count: int
    quality_score: float


@dataclass(slots=True)
class PdfExtractionDiagnostics:
    """
    PDF 파싱 선택 결과 및 후보 통계를 표현한다.

    Args:
        selected_parser (str): 최종 선택된 파서 이름.
        selected_quality_score (float): 선택 결과의 점수.
        selected_text_length (int): 선택 텍스트 길이.
        selected_hangul_count (int): 선택 텍스트의 한글 문자 수.
        candidates (list[ParserCandidateStats]): 파서 후보 통계 목록.
        errors (list[str]): 파서 실행 중 발생한 에러 목록.

    Returns:
        None: PDF 파싱 진단 객체를 생성한다.
    """

    selected_parser: str
    selected_quality_score: float
    selected_text_length: int
    selected_hangul_count: int
    candidates: list[ParserCandidateStats]
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        """
        진단 정보를 JSON 직렬화 가능한 딕셔너리로 변환한다.

        Args:
            None

        Returns:
            dict[str, object]: 직렬화 가능한 진단 정보.
        """
        return {
            "selected_parser": self.selected_parser,
            "selected_quality_score": self.selected_quality_score,
            "selected_text_length": self.selected_text_length,
            "selected_hangul_count": self.selected_hangul_count,
            "candidates": [asdict(candidate) for candidate in self.candidates],
            "errors": list(self.errors),
        }


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    PDF 파일에서 텍스트를 추출한다.

    Args:
        pdf_path (Path): 추출할 PDF 파일 경로.

    Returns:
        str: 추출된 전체 텍스트.
    """
    text, _ = extract_text_from_pdf_with_diagnostics(pdf_path)
    return text


def extract_text_from_pdf_with_diagnostics(
    pdf_path: Path,
) -> tuple[str, PdfExtractionDiagnostics]:
    """
    PDF 텍스트를 추출하고 선택 과정의 품질 진단 정보를 함께 반환한다.

    Args:
        pdf_path (Path): 추출할 PDF 파일 경로.

    Returns:
        tuple[str, PdfExtractionDiagnostics]:
            선택된 텍스트와 진단 정보.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일이 존재하지 않습니다: {pdf_path}")

    candidates: list[tuple[str, str, ParserCandidateStats]] = []
    parser_errors: list[str] = []

    extractors: list[tuple[str, Callable[[Path], str]]] = [
        ("pdfplumber", _extract_with_pdfplumber),
        ("pymupdf", _extract_with_pymupdf),
    ]

    name: str
    extractor: Callable[[Path], str]
    for name, extractor in extractors:
        try:
            raw_text: str = extractor(pdf_path)
        except Exception as exc:
            parser_errors.append(f"{name}={exc}")
            continue

        normalized_text: str = _normalize_text(raw_text)
        if not normalized_text:
            continue

        (
            text_length,
            hangul_count,
            token_count,
            hangul_ratio,
            digit_ratio,
        ) = _compute_quality_metrics(normalized_text)
        quality_score: float = _score_text_quality(
            text_length=text_length,
            hangul_count=hangul_count,
            token_count=token_count,
            hangul_ratio=hangul_ratio,
            digit_ratio=digit_ratio,
        )
        stats = ParserCandidateStats(
            parser_name=name,
            text_length=text_length,
            hangul_count=hangul_count,
            hangul_ratio=hangul_ratio,
            digit_ratio=digit_ratio,
            token_count=token_count,
            quality_score=quality_score,
        )
        candidates.append((name, normalized_text, stats))

    if not candidates:
        detail: str = " | ".join(parser_errors) if parser_errors else "no_text"
        raise RuntimeError(f"PDF 텍스트 추출 실패: {pdf_path}, reason={detail}")

    best_name, best_text, best_stats = max(
        candidates,
        key=lambda item: item[2].quality_score,
    )
    diagnostics = PdfExtractionDiagnostics(
        selected_parser=best_name,
        selected_quality_score=best_stats.quality_score,
        selected_text_length=best_stats.text_length,
        selected_hangul_count=best_stats.hangul_count,
        candidates=[item[2] for item in candidates],
        errors=parser_errors,
    )
    return best_text, diagnostics


def _normalize_text(text: str) -> str:
    """
    PDF 추출 텍스트를 평가/활용하기 쉬운 형태로 정규화한다.

    Args:
        text (str): 추출된 원본 텍스트.

    Returns:
        str: 연속 공백이 정리된 텍스트.
    """
    return " ".join(text.split())


def _compute_quality_metrics(
    text: str,
) -> tuple[int, int, int, float, float]:
    """
    텍스트 품질 점수 계산에 필요한 기초 통계를 계산한다.

    Args:
        text (str): 정규화된 텍스트.

    Returns:
        tuple[int, int, int, float, float]:
            (전체길이, 한글수, 토큰수, 한글비율, 숫자비율)
    """
    total_len: int = len(text)
    if total_len == 0:
        return 0, 0, 0, 0.0, 0.0

    hangul_count: int = len(_HANGUL_PATTERN.findall(text))
    meaningful_count: int = len(_ALNUM_PATTERN.findall(text))
    digit_count: int = len(_DIGIT_PATTERN.findall(text))
    token_count: int = len(text.split())

    safe_meaningful: int = max(1, meaningful_count)
    hangul_ratio: float = hangul_count / safe_meaningful
    digit_ratio: float = digit_count / safe_meaningful
    return total_len, hangul_count, token_count, hangul_ratio, digit_ratio


def _score_text_quality(
    text_length: int,
    hangul_count: int,
    token_count: int,
    hangul_ratio: float,
    digit_ratio: float,
) -> float:
    """
    추출 텍스트의 품질을 점수화한다.

    점수 기준:
    1) 전체 길이
    2) 한글 비중
    3) 짧고 잡음 중심 텍스트 패널티

    Args:
        text (str): 정규화된 추출 텍스트.

    Returns:
        float: 품질 점수(높을수록 우수).
    """
    if text_length == 0:
        return 0.0

    score: float = float(text_length)
    score += float(hangul_count) * 4.0
    score += hangul_ratio * 500.0

    # 짧고 정보량이 낮은 차트 파편 텍스트를 강하게 감점한다.
    if text_length < 350 and hangul_count < 30:
        score -= 700.0

    if token_count < 45 and hangul_count < 20:
        score -= 450.0

    if digit_ratio > 0.72 and hangul_count < 80:
        score -= 350.0

    return score


def _extract_with_pdfplumber(pdf_path: Path) -> str:
    """
    pdfplumber를 이용해 PDF 텍스트를 추출한다.

    Args:
        pdf_path (Path): PDF 파일 경로.

    Returns:
        str: 페이지 결합 텍스트.
    """
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("pdfplumber 패키지가 설치되지 않았습니다.") from exc

    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text: str = page.extract_text(layout=True) or ""
            if page_text.strip():
                pages.append(page_text)

    return "\n\n".join(pages)


def _extract_with_pymupdf(pdf_path: Path) -> str:
    """
    PyMuPDF를 이용해 PDF 텍스트를 추출한다.

    Args:
        pdf_path (Path): PDF 파일 경로.

    Returns:
        str: 페이지 결합 텍스트.
    """
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF 패키지가 설치되지 않았습니다.") from exc

    pages: list[str] = []
    with fitz.open(pdf_path) as document:
        for page in document:
            page_text: str = page.get_text("text")
            if page_text.strip():
                pages.append(page_text)

    return "\n\n".join(pages)
