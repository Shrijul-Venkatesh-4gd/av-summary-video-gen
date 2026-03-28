from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SemanticColorRole = Literal[
    "focus",
    "secondary",
    "warning",
    "success",
    "active_path",
    "muted_structure",
]


@dataclass(frozen=True)
class ThemeColors:
    background: str = "#081018"
    panel: str = "#101A26"
    panel_alt: str = "#132133"
    text_primary: str = "#F3F4F6"
    text_secondary: str = "#B7C2D0"
    focus: str = "#7DD3FC"
    secondary: str = "#C4B5FD"
    warning: str = "#FB7185"
    success: str = "#4ADE80"
    active_path: str = "#FBBF24"
    muted_structure: str = "#395066"
    outline: str = "#5D7288"
    shadow: str = "#050A10"


@dataclass(frozen=True)
class ThemeTypography:
    title_font: str = "DejaVu Sans"
    body_font: str = "DejaVu Sans"
    mono_font: str = "DejaVu Sans Mono"
    display_xl: float = 1.12
    display_lg: float = 0.88
    heading_md: float = 0.64
    body_md: float = 0.4
    body_sm: float = 0.32
    label_xs: float = 0.24


@dataclass(frozen=True)
class ThemeSpacing:
    scene_margin: float = 0.7
    section_gap: float = 0.45
    card_gap: float = 0.28
    chip_gap: float = 0.16
    card_padding: float = 0.22
    panel_padding: float = 0.3
    corner_radius: float = 0.22


@dataclass(frozen=True)
class ThemeMotion:
    fast: float = 0.45
    medium: float = 0.8
    slow: float = 1.2
    pause: float = 0.3
    settle: float = 0.6


@dataclass(frozen=True)
class ThemeStroke:
    thin: float = 1.5
    medium: float = 2.0
    heavy: float = 3.0


@dataclass(frozen=True)
class ThemeDepth:
    background: int = 0
    structure: int = 5
    content: int = 20
    overlay: int = 40
    emphasis: int = 60


@dataclass(frozen=True)
class ExplainerTheme:
    colors: ThemeColors = ThemeColors()
    type: ThemeTypography = ThemeTypography()
    space: ThemeSpacing = ThemeSpacing()
    motion: ThemeMotion = ThemeMotion()
    stroke: ThemeStroke = ThemeStroke()
    depth: ThemeDepth = ThemeDepth()


THEME = ExplainerTheme()
SCENE_ACCENT_LIMIT = 2

SEMANTIC_COLOR_MAP: dict[SemanticColorRole, str] = {
    "focus": THEME.colors.focus,
    "secondary": THEME.colors.secondary,
    "warning": THEME.colors.warning,
    "success": THEME.colors.success,
    "active_path": THEME.colors.active_path,
    "muted_structure": THEME.colors.muted_structure,
}


def get_semantic_color(role: SemanticColorRole | str, *, fallback: str | None = None) -> str:
    if role in SEMANTIC_COLOR_MAP:
        return SEMANTIC_COLOR_MAP[role]  # type: ignore[index]
    if fallback is not None and fallback in SEMANTIC_COLOR_MAP:
        return SEMANTIC_COLOR_MAP[fallback]  # type: ignore[index]
    return THEME.colors.focus


def theme_design_notes() -> list[str]:
    return [
        "Dark foundation with soft off-white text for long-form viewing comfort.",
        "Use at most one focus accent and one supporting accent in a scene.",
        "Narration carries the explanation; on-screen text acts as anchors and labels.",
        "Motion should reveal structure progressively and isolate the active idea.",
        "Keep spacing generous so one visual focus dominates at a time.",
    ]
