from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from utils.settings import MAX_OUTLINE_SECTIONS, MAX_TOTAL_LESSON_DURATION_SEC


class TeachingSection(BaseModel):
    section_id: str = Field(description="Stable identifier such as section_01")
    section_title: str = Field(description="Short student-friendly title")
    learning_objective: str = Field(
        description="What a beginner should understand after this section"
    )
    main_idea: str = Field(
        description="Exactly one core idea that anchors the section"
    )
    hook: str = Field(
        description="Short hook, puzzle, or motivating question that opens the section"
    )
    intuition: str = Field(
        description="Simple intuition that makes the idea feel concrete before formal detail"
    )
    explanation: str = Field(
        description="Beginner-friendly explanation grounded in the source material"
    )
    concrete_example: str = Field(
        description="Faithful example introduced early to make the idea tangible"
    )
    misconception_to_avoid: str = Field(
        description="Likely misunderstanding to correct explicitly"
    )
    quick_recap: str = Field(
        description="Short recap line that reinforces the main idea"
    )
    on_screen_goal: str = Field(
        description="What the visuals should help the learner notice"
    )
    estimated_duration_sec: int = Field(
        ge=20,
        le=180,
        description="Estimated teaching time for this section in seconds",
    )
    source_references: list[str] = Field(
        default_factory=list,
        description="Grounding references such as filenames, page numbers, or section labels",
    )


class TeachingOutline(BaseModel):
    video_title: str = Field(description="Title of the lesson video")
    target_audience: str = Field(description="Who the lesson is designed for")
    lesson_goal: str = Field(description="Overall student outcome for the video")
    beginner_assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions about what the audience does or does not know",
    )
    teaching_strategy: str = Field(
        description="Short note on pacing, examples, and pedagogy for the lesson"
    )
    total_estimated_duration_sec: int = Field(
        ge=60,
        le=1800,
        description="Estimated total video duration in seconds",
    )
    sections: list[TeachingSection] = Field(
        min_length=1,
        description="Ordered teaching sections, each centered on one main idea",
    )

    @field_validator("sections")
    @classmethod
    def _limit_section_count(cls, value: list[TeachingSection]) -> list[TeachingSection]:
        if len(value) > MAX_OUTLINE_SECTIONS:
            raise ValueError(
                f"Teaching outline may include at most {MAX_OUTLINE_SECTIONS} sections."
            )
        return value

    @model_validator(mode="after")
    def _check_total_duration(self) -> "TeachingOutline":
        inferred_duration = sum(section.estimated_duration_sec for section in self.sections)
        if self.total_estimated_duration_sec > MAX_TOTAL_LESSON_DURATION_SEC:
            raise ValueError(
                f"Teaching outline exceeds the configured lesson duration limit of "
                f"{MAX_TOTAL_LESSON_DURATION_SEC} seconds."
            )
        if inferred_duration > MAX_TOTAL_LESSON_DURATION_SEC:
            raise ValueError(
                f"Teaching outline section durations exceed the configured lesson duration "
                f"limit of {MAX_TOTAL_LESSON_DURATION_SEC} seconds."
            )
        return self
