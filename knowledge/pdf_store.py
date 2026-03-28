from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai_like import OpenAILikeEmbedder
from agno.vectordb.pgvector import PgVector

from knowledge.pdf_reader import build_pdf_reader
from utils.settings import (
    AGNO_DB_URL,
    AGNO_TABLE_NAME,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_EMBED_DIMENSIONS,
    OPENROUTER_EMBED_MODEL,
    PDF_DIR,
    PROJECT_ROOT,
)

INGESTION_REGISTRY_PATH = PROJECT_ROOT / "generated" / "ingestion" / "registry.json"


@dataclass
class IngestionResult:
    pdf_dir: Path
    processed_files: list[Path]
    ingested_files: list[Path]
    skipped_files: list[Path]
    registry_path: Path

def get_db_url() -> str:
    return AGNO_DB_URL


def get_table_name() -> str:
    return AGNO_TABLE_NAME


def get_pdf_dir() -> str:
    return PDF_DIR


def build_knowledge() -> Knowledge:
    return Knowledge(
        vector_db=PgVector(
            table_name=get_table_name(),
            db_url=get_db_url(),
            embedder=OpenAILikeEmbedder(
                id=OPENROUTER_EMBED_MODEL,
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                dimensions=OPENROUTER_EMBED_DIMENSIONS,
            ),
        )
    )


def _compute_file_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _compute_path_content_hash(file_path: Path) -> str:
    return hashlib.sha256(str(file_path).encode()).hexdigest()


def _load_ingestion_registry(registry_path: Path | None = None) -> dict:
    target_path = registry_path or INGESTION_REGISTRY_PATH
    if not target_path.exists():
        return {"version": 1, "files": {}}

    try:
        return json.loads(target_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "files": {}}


def _save_ingestion_registry(registry: dict, registry_path: Path | None = None) -> Path:
    target_path = registry_path or INGESTION_REGISTRY_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return target_path


def ingest_pdfs(
    pdf_dir: str | None = None,
    *,
    force_reingest: bool = False,
    registry_path: str | Path | None = None,
) -> IngestionResult:
    source_dir = pdf_dir or get_pdf_dir()
    pdf_path = Path(source_dir).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF directory not found: {source_dir}")

    pdf_files = sorted(pdf_path.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {source_dir}")

    registry_file = Path(registry_path).expanduser().resolve() if registry_path else INGESTION_REGISTRY_PATH
    registry = _load_ingestion_registry(registry_file)
    file_index = registry.setdefault("files", {})

    knowledge = build_knowledge()
    reader = build_pdf_reader()
    ingested_files: list[Path] = []
    skipped_files: list[Path] = []

    for pdf_file in pdf_files:
        file_sha256 = _compute_file_sha256(pdf_file)
        path_content_hash = _compute_path_content_hash(pdf_file)
        record_key = str(pdf_file)
        existing_record = file_index.get(record_key)
        exists_in_vector_db = knowledge.vector_db.content_hash_exists(path_content_hash)

        if (
            not force_reingest
            and existing_record is not None
            and existing_record.get("sha256") == file_sha256
            and exists_in_vector_db
        ):
            print(f"Skipping unchanged PDF: {pdf_file}")
            skipped_files.append(pdf_file)
            continue

        print(f"Ingesting: {pdf_file}")
        knowledge.insert(
            path=str(pdf_file),
            reader=reader,
            upsert=True,
            skip_if_exists=False,
        )
        ingested_files.append(pdf_file)
        stat = pdf_file.stat()
        file_index[record_key] = {
            "sha256": file_sha256,
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "last_ingested_at": datetime.now(UTC).isoformat(),
        }

    saved_registry_path = _save_ingestion_registry(registry, registry_file)
    print(
        f"\nDone. Ingested {len(ingested_files)} PDF(s), skipped {len(skipped_files)} unchanged PDF(s) "
        f"for table '{get_table_name()}'."
    )
    return IngestionResult(
        pdf_dir=pdf_path,
        processed_files=pdf_files,
        ingested_files=ingested_files,
        skipped_files=skipped_files,
        registry_path=saved_registry_path,
    )


if __name__ == "__main__":
    ingest_pdfs(get_pdf_dir())
