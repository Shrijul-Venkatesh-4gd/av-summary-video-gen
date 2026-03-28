from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    severity: Literal["warning", "error"]
    code: str
    message: str
    scene_id: str | None = None
    field_name: str | None = None


class StoryboardValidationReport(BaseModel):
    valid: bool
    warning_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    issues: list[ValidationIssue] = Field(default_factory=list)
