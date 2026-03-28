from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.models.openai import OpenAIResponses

from models.builder_models import ManimVideoPlan
from models.narrator_models import NarrationScript, NarrationSection

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
OPENPEEPS_DIR = Path(
    os.getenv("OPENPEEPS_DIR", str(PROJECT_ROOT / "assets" / "openpeeps"))
)
GENERATED_MANIM_DIR = PROJECT_ROOT / "generated" / "manim"


# ----------------------------
# Agent builder
# ----------------------------

def build_manim_codegen_agent() -> Agent:
    return Agent(
        name="Manim Code Generator",
        model=OpenAIResponses(id=OPENAI_MODEL),
        output_schema=ManimVideoPlan,
        markdown=False,
        instructions=[
            "You generate clean Manim Community Edition Python code from a narration script.",
            "Generate one independent Scene subclass per narration section.",
            "Every scene must be visually simple, readable, and renderable.",
            "Prefer short, elegant animations over dense text blocks.",
            "Use local Open Peeps assets from the provided assets/openpeeps directory.",
            "Use SVGMobject for .svg assets and ImageMobject for .png assets.",
            "Do not assume internet access or remote asset downloads.",
            "Do not generate one giant monolithic Scene for the full video.",
            "Each scene should contain a complete class definition.",
            "Do not include import statements inside individual scene code strings.",
            "Keep font sizes, spacing, and layout sensible for 16:9 video.",
            "Use only broadly standard Manim APIs.",
            "Do not add voiceover code.",
            "Do not add ffmpeg code.",
            "Do not add shell commands.",
            "Return a valid Python filename ending in .py for module_name.",
            "Return valid Python identifiers for every class_name.",
            "Return syntactically valid Python in each scene code string.",
            f"Assume Open Peeps assets live under: {OPENPEEPS_DIR}",
            "If a scene benefits from a person/teacher character, include an Open Peeps asset.",
            "If a scene does not need a character, do not force one in.",
        ],
    )


# ----------------------------
# Prompting helper
# ----------------------------

def build_manim_prompt(narration: NarrationScript) -> str:
    return f"""
Convert this narration script into scene-by-scene Manim code.

Requirements:
1. Generate one Scene subclass per narration section.
2. Use local Open Peeps assets when a human figure improves the scene.
3. Prefer SVG assets when possible.
4. Keep each scene visually uncluttered and likely to render successfully.
5. Use titles, diagrams, arrows, grouped labels, and simple transitions.
6. Do not generate audio logic.
7. Do not generate video stitching logic.
8. The code should target Manim Community Edition.
9. The final output must match the provided output schema.
10. Do not include import statements inside each scene code block.

Narration script:
{narration.model_dump_json(indent=2)}
"""


def _coerce_manim_plan(content: Any) -> ManimVideoPlan:
    if isinstance(content, ManimVideoPlan):
        return content
    if isinstance(content, dict):
        return ManimVideoPlan.model_validate(content)
    if isinstance(content, str):
        return ManimVideoPlan.model_validate_json(content)
    raise TypeError(f"Unexpected Manim response type: {type(content)!r}")


def generate_manim_plan(narration: NarrationScript) -> ManimVideoPlan:
    agent = build_manim_codegen_agent()
    prompt = build_manim_prompt(narration)
    response = agent.run(prompt)
    return _coerce_manim_plan(response.content)


# ----------------------------
# Save generated code to disk
# ----------------------------

def _normalize_module_name(module_name: str) -> str:
    filename = Path(module_name).name
    if not filename.endswith(".py"):
        filename = f"{filename}.py"
    return filename


def _strip_manim_imports(scene_code: str) -> str:
    lines = scene_code.strip().splitlines()
    filtered_lines = [
        line
        for line in lines
        if not line.strip().startswith("from manim import")
        and not line.strip().startswith("import manim")
    ]
    return "\n".join(filtered_lines).strip()


def save_manim_plan(
    plan: ManimVideoPlan,
    out_dir: str | Path = GENERATED_MANIM_DIR,
) -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    module_path = out_path / _normalize_module_name(plan.module_name)
    with module_path.open("w", encoding="utf-8") as f:
        f.write("from manim import *\n\n")
        for scene in plan.scenes:
            f.write(_strip_manim_imports(scene.code))
            f.write("\n\n")

    print(f"Saved generated Manim module to: {module_path}")
    return module_path


# ----------------------------
# Example usage
# ----------------------------

if __name__ == "__main__":
    narration = NarrationScript(
        video_title="Computational Problem Solving Summary",
        target_audience="first-year students",
        total_duration_sec=180,
        summary="An intro to computational problem solving, representation, algorithm, and brute force.",
        sections=[
            NarrationSection(
                title="What is Computational Problem Solving?",
                duration_sec=45,
                narration=(
                    "Computational problem solving is about representing a problem clearly "
                    "and designing an algorithm that solves it step by step."
                ),
                visual_notes=[
                    "Show title",
                    "Show problem box transforming into representation and algorithm",
                    "Use teacher figure on one side"
                ],
                source_refs=["python-intro-1.pdf p.14", "python-intro-2.pdf p.9"]
            ),
            NarrationSection(
                title="Brute Force Example",
                duration_sec=60,
                narration=(
                    "A classic example is the man, cabbage, goat, and wolf problem. "
                    "One simple method is brute force: try valid possibilities until the goal is reached."
                ),
                visual_notes=[
                    "River with east and west banks",
                    "Icons for man, goat, wolf, cabbage",
                    "Animate one crossing at a time"
                ],
                source_refs=["python-intro-1.pdf p.19-22", "python-intro-2.pdf p.12-16"]
            )
        ]
    )

    plan = generate_manim_plan(narration)
    print(plan.model_dump_json(indent=2))
    save_manim_plan(plan)
