from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SceneType = Literal[
    "title_card",
    "hook_question",
    "concept_map",
    "step_by_step_reveal",
    "comparison",
    "worked_example",
    "state_transition",
    "code_demo",
    "diagram_explainer",
    "process_flow",
    "recap_card",
    "quiz_pause",
    "summary_board",
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
