"""Extract text from a PDF, one entry per page."""

import logging

import fitz  # PyMuPDF

from data_models import PageText

logger = logging.getLogger(__name__)


def load_pdf(path: str) -> list[PageText]:
    logger.info("Opening PDF path=%s", path)
    document = fitz.open(path)
    try:
        pages = [
            PageText(page_number=page_number, text=page.get_text("text"))
            for page_number, page in enumerate(document, start=1)
        ]
    finally:
        document.close()

    # Drop blank pages (e.g. scanned images with no extractable text) -
    # nothing useful to chunk or embed there.
    text_pages = [page for page in pages if page.text.strip()]
    logger.info(
        "PDF text extraction completed pages=%d text_pages=%d",
        len(pages),
        len(text_pages),
    )
    return text_pages
