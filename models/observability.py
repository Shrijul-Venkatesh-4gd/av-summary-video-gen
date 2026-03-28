from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedSourceChunk(BaseModel):
    chunk_id: str
    document_name: str
    locator: str
    similarity_score: float | None = Field(default=None, ge=0, le=1)
    token_estimate: int = Field(ge=0)
    character_count: int = Field(ge=0)
    content: str


class RetrievalStats(BaseModel):
    query: str
    retrieval_calls: int = Field(ge=0)
    max_retrieval_calls: int = Field(ge=1)
    candidate_chunks: int = Field(ge=0)
    deduplicated_chunks: int = Field(ge=0)
    selected_chunks: int = Field(ge=0)
    source_tokens_estimate: int = Field(ge=0)
    source_characters: int = Field(ge=0)
    max_retrieved_chunks: int = Field(ge=1)
    max_source_tokens: int = Field(ge=1)
    max_source_characters: int = Field(ge=1)
    search_candidates: int = Field(ge=1)
    compression_applied: bool = False
    truncation_applied: bool = False
    warnings: list[str] = Field(default_factory=list)


class StageMetrics(BaseModel):
    stage_name: str
    model: str
    input_tokens_estimate: int = Field(ge=0)
    input_tokens_limit: int = Field(ge=0)
    output_tokens_estimate: int = Field(ge=0)
    output_tokens_limit: int = Field(ge=0)
    serialized_artifact_bytes: int = Field(ge=0)
    compression_applied: bool = False
    truncation_applied: bool = False
    warnings: list[str] = Field(default_factory=list)


class WorkflowManifestMetadata(BaseModel):
    retrieval_stats: RetrievalStats | None = None
    stage_metrics: list[StageMetrics] = Field(default_factory=list)
    compression_decisions: list[str] = Field(default_factory=list)
    truncation_decisions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
