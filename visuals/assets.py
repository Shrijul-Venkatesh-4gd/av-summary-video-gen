from __future__ import annotations

from typing import Callable

from manim import DOWN, Circle, Line, Polygon, Rectangle, RoundedRectangle, Text, VGroup

from visuals.theme import THEME, get_semantic_color


ASSET_CATALOG: dict[str, dict[str, str]] = {
    "computer_icon": {
        "purpose": "Marks machines, runtime environments, or digital systems.",
        "manim_strategy": "Use a rounded monitor, a short stand, and a subtle status light.",
    },
    "code_icon": {
        "purpose": "Signals code-centric explanation without a literal screenshot.",
        "manim_strategy": "Use angle-bracket strokes inside a rounded panel.",
    },
    "document_icon": {
        "purpose": "Represents notes, source documents, or outputs.",
        "manim_strategy": "Use a rounded page with stacked content lines and a folded corner cue.",
    },
    "student_character": {
        "purpose": "Represents learner questions or prediction moments.",
        "manim_strategy": "Use a simple head-and-shoulders silhouette with neutral geometry.",
    },
    "teacher_character": {
        "purpose": "Represents guided explanation or instructor hints.",
        "manim_strategy": "Use a similar silhouette plus a small pointer accent.",
    },
    "warning_icon": {
        "purpose": "Flags invalid states, pitfalls, or misconceptions.",
        "manim_strategy": "Use a warning triangle with an exclamation mark.",
    },
    "check_icon": {
        "purpose": "Marks correct understanding or solved states.",
        "manim_strategy": "Use a circle badge with a geometric check stroke.",
    },
    "flow_icon": {
        "purpose": "Hints at pipelines, transformations, or process stages.",
        "manim_strategy": "Use three nodes connected by clean lines.",
    },
}


def _label(text: str) -> Text:
    return Text(
        text,
        font=THEME.type.body_font,
        color=THEME.colors.text_secondary,
        font_size=20,
    )


def build_computer_icon() -> VGroup:
    frame = RoundedRectangle(
        width=1.8,
        height=1.15,
        corner_radius=0.12,
        fill_color=THEME.colors.panel_alt,
        fill_opacity=1,
        stroke_color=THEME.colors.outline,
        stroke_width=THEME.stroke.medium,
    )
    stand = Rectangle(
        width=0.18,
        height=0.25,
        fill_color=THEME.colors.outline,
        fill_opacity=1,
        stroke_width=0,
    ).next_to(frame, DOWN, buff=0.02)
    base = RoundedRectangle(
        width=0.82,
        height=0.12,
        corner_radius=0.06,
        fill_color=THEME.colors.outline,
        fill_opacity=1,
        stroke_width=0,
    ).next_to(stand, DOWN, buff=0.02)
    light = Circle(
        radius=0.04,
        fill_color=get_semantic_color("focus"),
        fill_opacity=1,
        stroke_width=0,
    ).move_to(frame.get_corner([1, -1, 0]) + [-0.16, 0.12, 0])
    return VGroup(frame, stand, base, light)


def build_code_icon() -> VGroup:
    panel = RoundedRectangle(
        width=1.7,
        height=1.1,
        corner_radius=0.12,
        fill_color=THEME.colors.panel_alt,
        fill_opacity=1,
        stroke_color=THEME.colors.outline,
        stroke_width=THEME.stroke.medium,
    )
    left = VGroup(
        Line([-0.3, 0.16, 0], [-0.55, 0, 0], color=get_semantic_color("focus"), stroke_width=THEME.stroke.heavy),
        Line([-0.55, 0, 0], [-0.3, -0.16, 0], color=get_semantic_color("focus"), stroke_width=THEME.stroke.heavy),
    )
    right = VGroup(
        Line([0.3, 0.16, 0], [0.55, 0, 0], color=get_semantic_color("secondary"), stroke_width=THEME.stroke.heavy),
        Line([0.55, 0, 0], [0.3, -0.16, 0], color=get_semantic_color("secondary"), stroke_width=THEME.stroke.heavy),
    )
    slash = Line(
        [-0.06, -0.22, 0],
        [0.08, 0.22, 0],
        color=THEME.colors.text_secondary,
        stroke_width=THEME.stroke.medium,
    )
    return VGroup(panel, left, right, slash)


def build_document_icon() -> VGroup:
    page = RoundedRectangle(
        width=1.45,
        height=1.85,
        corner_radius=0.12,
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=THEME.colors.outline,
        stroke_width=THEME.stroke.medium,
    )
    lines = VGroup(
        *[
            Line(
                [-0.42, 0.45 - (index * 0.25), 0],
                [0.36, 0.45 - (index * 0.25), 0],
                color=THEME.colors.text_secondary,
                stroke_width=THEME.stroke.thin,
            )
            for index in range(4)
        ]
    )
    fold = Polygon(
        [0.3, 0.92, 0],
        [0.52, 0.92, 0],
        [0.52, 0.68, 0],
        color=THEME.colors.outline,
        fill_color=THEME.colors.panel_alt,
        fill_opacity=1,
        stroke_width=THEME.stroke.thin,
    )
    return VGroup(page, lines, fold)


def build_student_character() -> VGroup:
    head = Circle(
        radius=0.22,
        fill_color=THEME.colors.panel_alt,
        fill_opacity=1,
        stroke_color=THEME.colors.outline,
        stroke_width=THEME.stroke.medium,
    )
    torso = Line([0, -0.24, 0], [0, -0.82, 0], color=THEME.colors.text_secondary, stroke_width=THEME.stroke.medium)
    shoulders = Line([-0.34, -0.44, 0], [0.34, -0.44, 0], color=THEME.colors.text_secondary, stroke_width=THEME.stroke.medium)
    return VGroup(head, torso, shoulders)


def build_teacher_character() -> VGroup:
    student = build_student_character()
    pointer = Line([0.26, -0.5, 0], [0.7, -0.1, 0], color=get_semantic_color("focus"), stroke_width=THEME.stroke.medium)
    return VGroup(student, pointer)


def build_warning_icon() -> VGroup:
    triangle = Polygon(
        [0, 0.62, 0],
        [-0.54, -0.44, 0],
        [0.54, -0.44, 0],
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=get_semantic_color("warning"),
        stroke_width=THEME.stroke.heavy,
    )
    exclamation = VGroup(
        Line([0, 0.22, 0], [0, -0.1, 0], color=get_semantic_color("warning"), stroke_width=THEME.stroke.heavy),
        Circle(radius=0.05, fill_color=get_semantic_color("warning"), fill_opacity=1, stroke_width=0).move_to([0, -0.24, 0]),
    )
    return VGroup(triangle, exclamation)


def build_check_icon() -> VGroup:
    circle = Circle(
        radius=0.55,
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=get_semantic_color("success"),
        stroke_width=THEME.stroke.heavy,
    )
    tick = VGroup(
        Line([-0.24, 0.0, 0], [-0.04, -0.22, 0], color=get_semantic_color("success"), stroke_width=THEME.stroke.heavy),
        Line([-0.04, -0.22, 0], [0.28, 0.2, 0], color=get_semantic_color("success"), stroke_width=THEME.stroke.heavy),
    )
    return VGroup(circle, tick)


def build_flow_icon() -> VGroup:
    nodes = VGroup(
        Circle(radius=0.14, fill_color=THEME.colors.panel_alt, fill_opacity=1, stroke_color=get_semantic_color("focus"), stroke_width=THEME.stroke.medium),
        Circle(radius=0.14, fill_color=THEME.colors.panel_alt, fill_opacity=1, stroke_color=get_semantic_color("active_path"), stroke_width=THEME.stroke.medium),
        Circle(radius=0.14, fill_color=THEME.colors.panel_alt, fill_opacity=1, stroke_color=get_semantic_color("success"), stroke_width=THEME.stroke.medium),
    ).arrange(buff=0.42)
    links = VGroup(
        Line(nodes[0].get_right(), nodes[1].get_left(), color=THEME.colors.outline, stroke_width=THEME.stroke.medium),
        Line(nodes[1].get_right(), nodes[2].get_left(), color=THEME.colors.outline, stroke_width=THEME.stroke.medium),
    )
    return VGroup(nodes, links)


ASSET_BUILDERS: dict[str, Callable[[], VGroup]] = {
    "computer_icon": build_computer_icon,
    "code_icon": build_code_icon,
    "document_icon": build_document_icon,
    "student_character": build_student_character,
    "teacher_character": build_teacher_character,
    "warning_icon": build_warning_icon,
    "check_icon": build_check_icon,
    "flow_icon": build_flow_icon,
}


def build_asset(asset_id: str, *, with_label: bool = False) -> VGroup:
    builder = ASSET_BUILDERS.get(asset_id)
    if builder is None:
        fallback = VGroup(build_document_icon(), _label(asset_id.replace("_", " ")))
        return fallback.arrange(DOWN, buff=0.16)
    asset = builder()
    if not with_label:
        return asset
    label = _label(asset_id.replace("_", " "))
    return VGroup(asset, label).arrange(DOWN, buff=0.14)


def format_asset_catalog_for_prompt() -> str:
    return "\n".join(
        f"- {asset_id}: {spec['purpose']} Primitive-friendly build: {spec['manim_strategy']}"
        for asset_id, spec in ASSET_CATALOG.items()
    )
