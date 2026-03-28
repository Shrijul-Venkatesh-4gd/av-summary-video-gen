from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from utils.budgeting import count_words
from utils.settings import (
    MAX_ON_SCREEN_WORDS_PER_SCENE,
    MAX_SCENE_NARRATION_WORDS,
    MAX_STORYBOARD_SCENES,
    MAX_TOTAL_LESSON_DURATION_SEC,
)


SceneType = Literal[
    "title_card",
    "title_intro",
    "hook_question",
    "concept_build",
    "concept_map",
    "step_by_step_reveal",
    "comparison",
    "worked_example",
    "state_transition",
    "code_demo",
    "code_walkthrough",
    "diagram_explainer",
    "process_flow",
    "recap_card",
    "quiz_pause",
    "summary_board",
]

SemanticColorRole = Literal[
    "focus",
    "secondary",
    "warning",
    "success",
    "active_path",
    "muted_structure",
]


class AssetRequirement(BaseModel):
    asset_id: str = Field(
        description="Reusable symbolic asset name, such as python_logo or warning_icon"
    )
    purpose: str = Field(
        description="Why the asset helps learning in this scene"
    )
    optional: bool = Field(
        default=True,
        description="Whether the scene can still work if the asset is omitted",
    )


class SemanticColorAssignment(BaseModel):
    role: SemanticColorRole = Field(
        description="Semantic color role applied consistently in the scene"
    )
    target: str = Field(
        description="Concept, label, or relation that should receive this color role"
    )


class StoryboardScene(BaseModel):
    scene_id: str = Field(description="Stable identifier such as scene_01")
    scene_title: str = Field(description="Short human-readable scene title")
    scene_type: SceneType
    learning_goal: str = Field(description="Single idea the learner should get from this scene")
    narration_text: str = Field(
        description="Narration for the scene. The narration does most of the explaining."
    )
    on_screen_text: list[str] = Field(
        default_factory=list,
        description="Short supporting text fragments suitable for readable captions or labels",
    )
    key_terms: list[str] = Field(
        default_factory=list,
        description="Short concept labels that can become nodes, chips, or anchors in the scene",
    )
    visual_strategy: str = Field(
        description="How the visual layout teaches the idea"
    )
    animation_plan: list[str] = Field(
        min_length=1,
        description="Ordered animation beats describing how elements appear or change",
    )
    layout_style: str = Field(
        description="Layout pattern, such as split_focus, center_with_callout, or left_diagram_right_labels"
    )
    emphasis_targets: list[str] = Field(
        default_factory=list,
        description="Words or elements that should receive visual emphasis",
    )
    visual_focus: str = Field(
        description="The single main visual object, relation, or contrast the learner should notice first"
    )
    semantic_color_roles: list[SemanticColorAssignment] = Field(
        default_factory=list,
        description="Explicit semantic color mapping for important concepts or relations in the scene",
    )
    estimated_duration_sec: int = Field(
        ge=8,
        le=90,
        description="Estimated scene duration in seconds",
    )
    transition_style: str = Field(
        description="How the scene enters or exits relative to its neighbors"
    )
    asset_requirements: list[AssetRequirement] = Field(
        default_factory=list,
        description="Optional reusable assets requested by the scene",
    )
    pedagogical_role: str = Field(
        description="Why the scene exists instructionally, such as hook, explain, contrast, or recap"
    )
    source_references: list[str] = Field(
        default_factory=list,
        description="Grounding references back to the source material",
    )
    attention_reset: bool = Field(
        default=False,
        description="Whether the scene intentionally resets learner attention",
    )
    variation_justification: str | None = Field(
        default=None,
        description="Why a repeated layout or scene type is justified here",
    )

    @field_validator("narration_text")
    @classmethod
    def _limit_narration_words(cls, value: str) -> str:
        if count_words(value) > MAX_SCENE_NARRATION_WORDS:
            raise ValueError(
                f"Storyboard narration must stay within {MAX_SCENE_NARRATION_WORDS} words per scene."
            )
        return value

    @field_validator("on_screen_text")
    @classmethod
    def _limit_on_screen_words(cls, value: list[str]) -> list[str]:
        total_words = sum(count_words(line) for line in value)
        if total_words > MAX_ON_SCREEN_WORDS_PER_SCENE:
            raise ValueError(
                f"Storyboard on-screen text must stay within {MAX_ON_SCREEN_WORDS_PER_SCENE} "
                "words per scene."
            )
        return value

    @field_validator("visual_focus")
    @classmethod
    def _require_visual_focus(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Storyboard scenes must define a clear visual_focus.")
        return value

    @field_validator("semantic_color_roles")
    @classmethod
    def _require_semantic_colors(cls, value: list[SemanticColorAssignment]) -> list[SemanticColorAssignment]:
        if not value:
            raise ValueError("Storyboard scenes must assign at least one semantic color role.")
        return value


class Storyboard(BaseModel):
    video_title: str = Field(description="Title of the lesson video")
    target_audience: str = Field(description="Who the storyboard is for")
    storyboard_goal: str = Field(
        description="How the storyboard should help students learn"
    )
    visual_language: list[str] = Field(
        default_factory=list,
        description="Shared visual-language notes for the overall lesson",
    )
    pacing_notes: list[str] = Field(
        default_factory=list,
        description="Notes on pacing, attention resets, and cognitive load management",
    )
    total_estimated_duration_sec: int = Field(
        ge=60,
        le=1800,
        description="Estimated total duration in seconds",
    )
    scenes: list[StoryboardScene] = Field(
        min_length=1,
        description="Ordered storyboard scenes for the lesson",
    )

    @field_validator("scenes")
    @classmethod
    def _limit_scene_count(cls, value: list[StoryboardScene]) -> list[StoryboardScene]:
        if len(value) > MAX_STORYBOARD_SCENES:
            raise ValueError(
                f"Storyboard may include at most {MAX_STORYBOARD_SCENES} scenes."
            )
        return value

    @model_validator(mode="after")
    def _check_total_duration(self) -> "Storyboard":
        inferred_duration = sum(scene.estimated_duration_sec for scene in self.scenes)
        if self.total_estimated_duration_sec > MAX_TOTAL_LESSON_DURATION_SEC:
            raise ValueError(
                f"Storyboard exceeds the configured lesson duration limit of "
                f"{MAX_TOTAL_LESSON_DURATION_SEC} seconds."
            )
        if inferred_duration > MAX_TOTAL_LESSON_DURATION_SEC:
            raise ValueError(
                f"Storyboard scene durations exceed the configured lesson duration limit "
                f"of {MAX_TOTAL_LESSON_DURATION_SEC} seconds."
            )
        return self
