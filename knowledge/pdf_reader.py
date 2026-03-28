from __future__ import annotations

import os

from agno.knowledge.reader.pdf_reader import PDFReader


PDF_CHUNK_SIZE = int(os.getenv("PDF_CHUNK_SIZE", "3000"))
PDF_SPLIT_ON_PAGES = os.getenv("PDF_SPLIT_ON_PAGES", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def build_pdf_reader(
    chunk_size: int = PDF_CHUNK_SIZE,
    split_on_pages: bool = PDF_SPLIT_ON_PAGES,
) -> PDFReader:
    return PDFReader(
        chunk_size=chunk_size,
        split_on_pages=split_on_pages,
    )
