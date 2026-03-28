from typing import Any

from pydantic import BaseModel, Field

from models.storyboard import Storyboard
from models.teaching_outline import TeachingOutline


class IngestRequest(BaseModel):
    pdf_dir: str | None = Field(
        default=None,
        description="Directory containing PDF files to ingest. Defaults to PDF_DIR from the environment.",
    )
    force_reingest: bool = Field(
        default=False,
        description="Reprocess PDFs even when they match the last ingested file fingerprint for the same path.",
    )


class OutlineRequest(BaseModel):
    topic: str
    audience: str = "students"
    duration_min: int = Field(default=5, ge=1)


class NarrateRequest(OutlineRequest):
    """Compatibility alias for the older narration endpoint."""


class StoryboardRequest(BaseModel):
    teaching_outline: TeachingOutline
    out_dir: str | None = Field(
        default=None,
        description="Optional root directory where the generated artifact bundle should be written.",
    )


class BuildRequest(BaseModel):
    storyboard: Storyboard
    out_dir: str | None = Field(
        default=None,
        description="Optional root directory where the generated artifact bundle should be written.",
    )


class WorkflowRequest(BaseModel):
    topic: str
    audience: str = "students"
    duration_min: int = Field(default=5, ge=1)
    run_ingestion: bool = False
    pdf_dir: str | None = Field(
        default=None,
        description="Directory containing PDF files to ingest when run_ingestion is true.",
    )
    force_reingest: bool = Field(
        default=False,
        description="Reprocess PDFs even when they match the last ingested file fingerprint for the same path.",
    )
    out_dir: str | None = Field(
        default=None,
        description="Optional root directory where the generated artifact bundle should be written.",
    )


class ArtifactManifest(BaseModel):
    endpoint: str
    run_id: str
    created_at: str
    artifact_dir: str
    request_path: str
    artifacts: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactResponse(BaseModel):
    endpoint: str
    run_id: str
    artifact_dir: str
    manifest_path: str
    artifacts: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
