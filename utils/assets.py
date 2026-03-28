from __future__ import annotations


ASSET_CATALOG: dict[str, dict[str, str]] = {
    "python_logo": {
        "purpose": "Signals Python-specific content quickly.",
        "manim_strategy": "Use two interlocking rounded rectangles with a small dot accent instead of an external logo file.",
    },
    "computer_icon": {
        "purpose": "Marks machines, terminals, or runtime environments.",
        "manim_strategy": "Use a monitor rectangle with a stand and a small status light.",
    },
    "arrow_flow": {
        "purpose": "Connects steps in a process or state transition.",
        "manim_strategy": "Use Arrow or CurvedArrow with short labels placed above the path.",
    },
    "student_character": {
        "purpose": "Represents a learner viewpoint in prompts or misconceptions.",
        "manim_strategy": "Use a lightweight stick figure or circular head with torso lines and a label.",
    },
    "teacher_character": {
        "purpose": "Represents guidance or coaching moments.",
        "manim_strategy": "Use a simple figure with a pointer or speech callout built from primitives.",
    },
    "warning_icon": {
        "purpose": "Flags mistakes, pitfalls, or misconceptions.",
        "manim_strategy": "Use a triangle or rounded square badge with an exclamation mark.",
    },
    "check_icon": {
        "purpose": "Marks correct understanding or verified results.",
        "manim_strategy": "Use a green circle or rounded square with a check mark made from Line segments.",
    },
}


def format_asset_catalog_for_prompt() -> str:
    lines = []
    for asset_id, spec in ASSET_CATALOG.items():
        lines.append(
            f"- {asset_id}: {spec['purpose']} Primitive-friendly build: {spec['manim_strategy']}"
        )
    return "\n".join(lines)
