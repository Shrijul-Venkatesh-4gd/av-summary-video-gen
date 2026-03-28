from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class SceneAsset(BaseModel):
    asset_path: str = Field(
        description="Relative local asset path, usually under assets/openpeeps"
    )
    asset_type: str = Field(description="svg or png")
    purpose: str = Field(description="Why this asset is used in the scene")


class SceneCode(BaseModel):
    scene_id: str = Field(description="Stable scene identifier like scene_01")
    class_name: str = Field(description="Python class name for the Manim scene")
    title: str = Field(description="Human-readable scene title")
    estimated_duration_sec: int = Field(ge=10, le=180)
    assets: List[SceneAsset] = Field(default_factory=list)
    code: str = Field(
        description="Complete Python code for a single Manim Scene subclass"
    )


class ManimVideoPlan(BaseModel):
    module_name: str = Field(
        description="Suggested output Python filename ending in .py"
    )
    shared_notes: List[str] = Field(default_factory=list)
    scenes: List[SceneCode]
