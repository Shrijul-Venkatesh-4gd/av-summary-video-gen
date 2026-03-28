from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


def _getenv(key: str, default: str) -> str:
    from os import getenv

    return getenv(key, default)


def _getbool(key: str, default: bool) -> bool:
    fallback = "true" if default else "false"
    return _getenv(key, fallback).lower() in {"1", "true", "yes", "on"}


OPENROUTER_API_KEY = _getenv("OPENROUTER_API_KEY", _getenv("GEMINI_API_KEY", ""))
OPENROUTER_BASE_URL = _getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = _getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_EMBED_MODEL = _getenv("OPENROUTER_EMBED_MODEL", "openai/text-embedding-3-small")
OPENROUTER_EMBED_DIMENSIONS = int(_getenv("OPENROUTER_EMBED_DIMENSIONS", "1536"))
AGNO_DB_URL = _getenv("AGNO_DB_URL", "postgresql+psycopg://ai:ai@localhost:5532/ai")
AGNO_TABLE_NAME = _getenv("AGNO_TABLE_NAME", "video_pdf_knowledge")
PDF_DIR = _getenv("PDF_DIR", str(PROJECT_ROOT / "input" / "pdfs"))
PDF_CHUNK_SIZE = int(_getenv("PDF_CHUNK_SIZE", "3000"))
PDF_SPLIT_ON_PAGES = _getbool("PDF_SPLIT_ON_PAGES", True)
