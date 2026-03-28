from __future__ import annotations

import json
import re
from textwrap import indent

from models.builder import ManimVideoPlan, SceneCode
from models.storyboard import Storyboard, StoryboardScene
from visuals.scene_templates import (
    build_scene_template_brief,
    builder_shared_notes,
    template_name_for_scene_type,
)


TEMPLATE_BUILDER_MODEL_NAME = "template_builder_v1"


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "lesson"


def _camelize(value: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part) or "Scene"


def _scene_payload(scene: StoryboardScene) -> dict[str, object]:
    return {
        "scene_id": scene.scene_id,
        "scene_title": scene.scene_title,
        "scene_type": scene.scene_type,
        "learning_goal": scene.learning_goal,
        "narration_text": scene.narration_text,
        "on_screen_text": scene.on_screen_text,
        "key_terms": scene.key_terms,
        "emphasis_targets": scene.emphasis_targets,
        "visual_strategy": scene.visual_strategy,
        "animation_plan": scene.animation_plan,
        "layout_style": scene.layout_style,
        "transition_style": scene.transition_style,
        "asset_requirements": [asset.asset_id for asset in scene.asset_requirements],
        "pedagogical_role": scene.pedagogical_role,
        "estimated_duration_sec": scene.estimated_duration_sec,
        "visual_focus": scene.visual_focus,
        "semantic_color_roles": [
            assignment.model_dump(mode="json")
            for assignment in scene.semantic_color_roles
        ],
    }


def _scene_class_name(scene: StoryboardScene, index: int) -> str:
    prefix = f"Scene{index + 1:02d}"
    return f"{prefix}{_camelize(scene.scene_title)}"


def _scene_code(scene: StoryboardScene, class_name: str) -> str:
    payload = json.dumps(_scene_payload(scene), indent=2)
    payload_literal = indent(payload, " " * 16)
    return (
        f"class {class_name}(ExplainerScene):\n"
        "    def construct(self):\n"
        "        scene_spec = SceneSpec(\n"
        "            **json.loads(\n"
        "                '''\n"
        f"{payload_literal}\n"
        "                '''\n"
        "            )\n"
        "        )\n"
        "        render_storyboard_scene(self, scene_spec)\n"
    )


def build_scene_code(scene: StoryboardScene, index: int) -> SceneCode:
    class_name = _scene_class_name(scene, index)
    template_brief = build_scene_template_brief(scene)
    template_name = template_brief["template_name"]
    asset_plan = [
        f"{asset.asset_id}: {asset.purpose}" for asset in scene.asset_requirements
    ]
    asset_plan.append(
        f"Template dispatch: scene_type '{scene.scene_type}' renders via '{template_name}'."
    )
    return SceneCode(
        scene_id=scene.scene_id,
        storyboard_scene_id=scene.scene_id,
        class_name=class_name,
        title=scene.scene_title,
        scene_type=scene.scene_type,
        pedagogical_role=scene.pedagogical_role,
        layout_style=scene.layout_style,
        estimated_duration_sec=scene.estimated_duration_sec,
        animation_beats=scene.animation_plan,
        asset_plan=asset_plan,
        code=_scene_code(scene, class_name),
    )


def build_manim_video_plan(storyboard: Storyboard) -> ManimVideoPlan:
    scenes = [build_scene_code(scene, index) for index, scene in enumerate(storyboard.scenes)]
    style_notes = [
        "Deterministic template-driven Manim builder using a shared dark explainer theme.",
        "Semantic colors stay consistent across scenes via explicit storyboard color-role assignments.",
        "Templates favor diagrams, process boxes, comparisons, and worked examples over text slides.",
        *storyboard.visual_language[:4],
    ]
    return ManimVideoPlan(
        video_title=storyboard.video_title,
        module_name=f"{_slugify(storyboard.video_title)}_explainer.py",
        build_goal=storyboard.storyboard_goal,
        style_notes=style_notes,
        shared_notes=[
            *builder_shared_notes(),
            "Generated scene classes delegate rendering to visuals.scene_templates.SceneSpec.",
        ],
        scenes=scenes,
    )


__all__ = [
    "TEMPLATE_BUILDER_MODEL_NAME",
    "build_manim_video_plan",
    "build_scene_code",
    "template_name_for_scene_type",
]
