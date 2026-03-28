from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class NarrationSection(BaseModel):
    title: str = Field(description="Short section title for the narrated video section")
    duration_sec: int = Field(
        ge=20,
        le=180,
        description="Estimated spoken duration for this section in seconds",
    )
    narration: str = Field(
        description="Natural spoken narration for this section. Should sound like a teacher explaining the topic."
    )
    visual_notes: List[str] = Field(
        description="Short notes describing what should appear on screen while this narration plays"
    )
    source_refs: List[str] = Field(
        description="Grounding references such as file names, page numbers, or section labels from the knowledge base"
    )


class NarrationScript(BaseModel):
    video_title: str = Field(description="Title of the final video")
    target_audience: str = Field(description="Who the narration is for")
    total_duration_sec: int = Field(
        ge=60,
        le=1800,
        description="Estimated total duration in seconds",
    )
    summary: str = Field(description="2-4 sentence summary of what the video teaches")
    sections: List[NarrationSection] = Field(
        min_length=1,
        description="Ordered list of narrated sections",
    )
