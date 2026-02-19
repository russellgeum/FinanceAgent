"""금융 리포트 PDF 텍스트 추출 모듈."""

from __future__ import annotations

from pathlib import Path


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    PDF 파일에서 텍스트를 추출한다.

    Args:
        pdf_path (Path): 추출할 PDF 파일 경로.

    Returns:
        str: 추출된 전체 텍스트.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일이 존재하지 않습니다: {pdf_path}")

    try:
        text: str = _extract_with_pdfplumber(pdf_path)
        if text.strip():
            return text
    except Exception:
        pass

    text = _extract_with_pymupdf(pdf_path)
    if text.strip():
        return text

    raise RuntimeError(f"PDF 텍스트 추출 실패: {pdf_path}")


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
