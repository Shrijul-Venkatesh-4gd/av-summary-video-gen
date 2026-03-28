from pathlib import Path
import os

from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector

from knowledge.pdf_reader import build_pdf_reader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_URL = os.getenv("AGNO_DB_URL", "postgresql+psycopg://ai:ai@localhost:5532/ai")
TABLE_NAME = os.getenv("AGNO_TABLE_NAME", "video_pdf_knowledge")
PDF_DIR = os.getenv("PDF_DIR", str(PROJECT_ROOT / "input" / "pdfs"))


def build_knowledge() -> Knowledge:
    return Knowledge(
        vector_db=PgVector(
            table_name=TABLE_NAME,
            db_url=DB_URL,
        )
    )


def ingest_pdfs(pdf_dir: str = PDF_DIR) -> list[Path]:
    pdf_path = Path(pdf_dir).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    pdf_files = sorted(pdf_path.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {pdf_dir}")

    knowledge = build_knowledge()
    reader = build_pdf_reader()

    for pdf_file in pdf_files:
        print(f"Ingesting: {pdf_file}")
        knowledge.insert(
            path=str(pdf_file),
            reader=reader,
        )

    print(f"\nDone. Ingested {len(pdf_files)} PDF(s) into table '{TABLE_NAME}'.")
    return pdf_files


if __name__ == "__main__":
    ingest_pdfs(PDF_DIR)
