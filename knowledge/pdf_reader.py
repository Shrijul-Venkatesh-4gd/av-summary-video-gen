from agno.knowledge.reader.pdf_reader import PDFReader

from utils.settings import PDF_CHUNK_SIZE, PDF_SPLIT_ON_PAGES


def build_pdf_reader(
    chunk_size: int | None = None,
    split_on_pages: bool | None = None,
) -> PDFReader:
    return PDFReader(
        chunk_size=PDF_CHUNK_SIZE if chunk_size is None else chunk_size,
        split_on_pages=PDF_SPLIT_ON_PAGES if split_on_pages is None else split_on_pages,
    )
