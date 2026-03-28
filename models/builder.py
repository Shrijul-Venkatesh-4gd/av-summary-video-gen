from __future__ import annotations

from pydantic import BaseModel, Field

from models.storyboard import SceneType


class SceneCode(BaseModel):
    scene_id: str = Field(description="Stable scene identifier like scene_01")
    storyboard_scene_id: str = Field(
        description="Source storyboard scene identifier that this Manim scene implements"
    )
    class_name: str = Field(description="Python class name for the Manim scene")
    title: str = Field(description="Human-readable scene title")
    scene_type: SceneType
    pedagogical_role: str = Field(
        description="Instructional role inherited from the storyboard scene"
    )
    layout_style: str = Field(
        description="Layout approach chosen for the scene implementation"
    )
    estimated_duration_sec: int = Field(ge=10, le=180)
    animation_beats: list[str] = Field(
        default_factory=list,
        description="Short description of the main animation beats in the scene",
    )
    asset_plan: list[str] = Field(
        default_factory=list,
        description="How optional reusable assets are represented with Manim primitives",
    )
    code: str = Field(
        description="Complete Python code for a single Manim Scene subclass"
    )


class ManimVideoPlan(BaseModel):
    video_title: str = Field(description="Title of the lesson this plan renders")
    module_name: str = Field(
        description="Suggested output Python filename ending in .py"
    )
    build_goal: str = Field(
        description="How the generated Manim scenes should support learning"
    )
    style_notes: list[str] = Field(default_factory=list)
    shared_notes: list[str] = Field(default_factory=list)
    scenes: list[SceneCode]
