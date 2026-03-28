from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    Circumscribe,
    Create,
    FadeIn,
    FadeOut,
    FadeToColor,
    Indicate,
    LaggedStart,
    ReplacementTransform,
    Scene,
    Text,
    TransformMatchingShapes,
    VGroup,
    Write,
)

from models.storyboard import StoryboardScene
from visuals.assets import build_asset
from visuals.components import (
    body_text,
    label_text,
    make_callout_box,
    make_comparison_column,
    make_concept_node,
    make_connector,
    make_focus_outline,
    make_label_chip,
    make_process_box,
    make_quiz_prompt_card,
    make_recap_card,
    make_relation_line,
    make_remember_banner,
    make_state_box,
    make_title_block,
    make_warning_badge,
    make_code_panel,
)
from visuals.theme import THEME, get_semantic_color, theme_design_notes


@dataclass(frozen=True)
class SceneSpec:
    scene_id: str
    scene_title: str
    scene_type: str
    learning_goal: str
    narration_text: str
    on_screen_text: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)
    emphasis_targets: list[str] = field(default_factory=list)
    visual_strategy: str = ""
    animation_plan: list[str] = field(default_factory=list)
    layout_style: str = ""
    transition_style: str = ""
    asset_requirements: list[str] = field(default_factory=list)
    pedagogical_role: str = ""
    estimated_duration_sec: int = 0
    visual_focus: str = ""
    semantic_color_roles: list[dict[str, str]] = field(default_factory=list)


_ALIAS_TO_TEMPLATE = {
    "title_card": "title_intro",
    "hook_question": "hook_question",
    "diagram_explainer": "concept_build",
    "concept_map": "concept_map",
    "step_by_step_reveal": "step_by_step_reveal",
    "process_flow": "process_flow",
    "worked_example": "worked_example",
    "state_transition": "state_transition",
    "code_demo": "code_walkthrough",
    "comparison": "comparison",
    "recap_card": "recap_card",
    "quiz_pause": "quiz_pause",
    "summary_board": "summary_board",
}


SCENE_TEMPLATE_LIBRARY: dict[str, dict[str, Any]] = {
    "title_intro": {
        "goal": "Open a lesson with a strong title, a clear promise, and a calm visual anchor.",
        "expected_inputs": ["scene_title", "learning_goal", "pedagogical_role"],
        "layout_behavior": "Centered title block with one supporting promise card and optional small asset.",
        "preferred_components": ["title_block", "label_chip", "callout_box"],
        "animation_patterns": ["Fade in the framing chip first.", "Write the title cleanly.", "Reveal the promise card after the title settles."],
        "pacing_rules": ["Keep text minimal.", "Do not compete with the first narration line."],
        "text_limits": "Title plus one short promise or framing sentence.",
        "emphasis_behavior": "Reserve accent color for the framing chip or one keyword.",
        "scene_types": ["title_card"],
    },
    "hook_question": {
        "goal": "Start with a concrete question or contrast that pulls the learner forward.",
        "expected_inputs": ["on_screen_text", "visual_focus", "learning_goal"],
        "layout_behavior": "Large central question with one clue or hint placed lower in the frame.",
        "preferred_components": ["quiz_prompt_card", "remember_banner", "warning_badge"],
        "animation_patterns": ["Show the prompt first.", "Hold briefly.", "Reveal a clue or contrast after the pause."],
        "pacing_rules": ["One question only.", "Use whitespace to create tension."],
        "text_limits": "One prompt plus one short clue.",
        "emphasis_behavior": "Highlight the unknown, not every noun.",
        "scene_types": ["hook_question"],
    },
    "concept_build": {
        "goal": "Introduce a core concept first, then grow supporting structure around it.",
        "expected_inputs": ["visual_focus", "key_terms", "on_screen_text"],
        "layout_behavior": "Centered core node with two to four supporting nodes branching outward.",
        "preferred_components": ["concept_node", "connector", "label_chip"],
        "animation_patterns": ["Grow the central concept.", "Add branches one at a time.", "Fade inactive branches to muted tones while the active one is explained."],
        "pacing_rules": ["Build from simple to rich.", "Do not reveal all branches at once."],
        "text_limits": "Short terms or phrases only.",
        "emphasis_behavior": "Keep the active branch in the focus accent and demote others.",
        "scene_types": ["diagram_explainer"],
    },
    "concept_map": {
        "goal": "Show relationships among ideas as a structured map rather than a list.",
        "expected_inputs": ["visual_focus", "key_terms", "semantic_color_roles"],
        "layout_behavior": "Central concept with radial or side branches and relation lines.",
        "preferred_components": ["concept_node", "relation_line", "label_chip"],
        "animation_patterns": ["Reveal the hub.", "Draw links progressively.", "Use circumscribe or isolate animation on the branch being discussed."],
        "pacing_rules": ["Keep branch count modest.", "Preserve context while isolating one relation at a time."],
        "text_limits": "One short label per node.",
        "emphasis_behavior": "Active relationship gets the warm path color; background links stay muted.",
        "scene_types": ["concept_map"],
    },
    "step_by_step_reveal": {
        "goal": "Teach a sequence by keeping one current step active while preserving context.",
        "expected_inputs": ["on_screen_text", "animation_plan", "learning_goal"],
        "layout_behavior": "Ordered steps down one side with a larger focus panel for the current step.",
        "preferred_components": ["label_chip", "callout_box", "connector"],
        "animation_patterns": ["Reveal one step at a time.", "Move focus instead of resetting the whole scene.", "Dim completed steps rather than removing them."],
        "pacing_rules": ["Three to five steps works best.", "Maintain consistent spacing."],
        "text_limits": "Short step labels, not full explanations.",
        "emphasis_behavior": "Only the active step uses the focus accent.",
        "scene_types": ["step_by_step_reveal"],
    },
    "process_flow": {
        "goal": "Explain a pipeline or causal flow with visible stage-to-stage movement.",
        "expected_inputs": ["on_screen_text", "visual_focus", "asset_requirements"],
        "layout_behavior": "Left-to-right or top-to-bottom process boxes connected by arrows.",
        "preferred_components": ["process_box", "connector", "label_chip"],
        "animation_patterns": ["Create the structure first.", "Send attention along the path stage by stage.", "Use transform or color change for the active stage."],
        "pacing_rules": ["Avoid more than four stages on one screen.", "Narration should travel with the highlight."],
        "text_limits": "Short stage labels with optional one-line captions.",
        "emphasis_behavior": "Only the current stage and path segment get bright accent treatment.",
        "scene_types": ["process_flow"],
    },
    "worked_example": {
        "goal": "Walk the learner from input to transformation to result.",
        "expected_inputs": ["on_screen_text", "learning_goal", "emphasis_targets"],
        "layout_behavior": "Input, transformation, and output panels with explicit progression.",
        "preferred_components": ["callout_box", "connector", "remember_banner"],
        "animation_patterns": ["Present the input.", "Animate the transformation step.", "Land on the output with a confident summary."],
        "pacing_rules": ["Keep the example concrete.", "One example per scene."],
        "text_limits": "Three compact stages.",
        "emphasis_behavior": "Final result or solved state uses success styling.",
        "scene_types": ["worked_example"],
    },
    "state_transition": {
        "goal": "Clarify valid and invalid changes between states.",
        "expected_inputs": ["key_terms", "semantic_color_roles", "visual_focus"],
        "layout_behavior": "Spatially separated states with clearly distinct valid and invalid transitions.",
        "preferred_components": ["state_box", "connector", "warning_badge"],
        "animation_patterns": ["Show states first.", "Animate valid transitions.", "Reveal invalid transition separately with warning styling."],
        "pacing_rules": ["Do not overload the graph.", "Use red only for actual invalidity."],
        "text_limits": "Short state labels and one short caution.",
        "emphasis_behavior": "Valid path uses active or success colors; invalid path uses warning color.",
        "scene_types": ["state_transition"],
    },
    "code_walkthrough": {
        "goal": "Explain code in small guided chunks with a visible result or interpretation area.",
        "expected_inputs": ["on_screen_text", "animation_plan", "visual_focus"],
        "layout_behavior": "Code panel on one side and explanation or result panel on the other.",
        "preferred_components": ["code_panel", "callout_box", "label_chip"],
        "animation_patterns": ["Reveal the code panel.", "Shift highlight line by line or chunk by chunk.", "Update the explanation panel in sync."],
        "pacing_rules": ["Limit visible lines.", "Avoid full-screen code walls."],
        "text_limits": "Six or fewer compact lines plus one concise explanation panel.",
        "emphasis_behavior": "The active line gets the warm path highlight.",
        "scene_types": ["code_demo"],
    },
    "comparison": {
        "goal": "Make a contrast easy to perceive at a glance.",
        "expected_inputs": ["on_screen_text", "emphasis_targets", "visual_focus"],
        "layout_behavior": "Balanced left-right columns with one dominant contrast label.",
        "preferred_components": ["comparison_column", "label_chip", "remember_banner"],
        "animation_patterns": ["Build both columns.", "Highlight the key contrast.", "Finish with a synthesizing banner."],
        "pacing_rules": ["Compare one dimension at a time.", "Use visual symmetry to support reasoning."],
        "text_limits": "Two to three points per column.",
        "emphasis_behavior": "Reserve strong color for the decisive contrast.",
        "scene_types": ["comparison"],
    },
    "recap_card": {
        "goal": "Compress the last teaching beat into a memorable short recap.",
        "expected_inputs": ["on_screen_text", "learning_goal"],
        "layout_behavior": "One dominant recap card with two to four tightly edited takeaways.",
        "preferred_components": ["recap_card", "remember_banner"],
        "animation_patterns": ["Reveal the card.", "Bring takeaways in with a measured lag.", "Hold on the strongest takeaway."],
        "pacing_rules": ["Keep it brief.", "Use recap phrasing, not explanation phrasing."],
        "text_limits": "Two to four takeaways.",
        "emphasis_behavior": "Use success or focus accents only on the takeaway worth remembering most.",
        "scene_types": ["recap_card"],
    },
    "quiz_pause": {
        "goal": "Create a reflective pause before the answer or next explanation.",
        "expected_inputs": ["on_screen_text", "visual_focus"],
        "layout_behavior": "Centered prediction card with ample breathing room and delayed answer area.",
        "preferred_components": ["quiz_prompt_card", "callout_box"],
        "animation_patterns": ["Question first.", "Explicit pause.", "Answer reveal later as a clean card, not a text dump."],
        "pacing_rules": ["One prompt only.", "Let the viewer think before revealing."],
        "text_limits": "Question plus one short reveal.",
        "emphasis_behavior": "Use the active-path accent for the prompt state and success or focus for the reveal.",
        "scene_types": ["quiz_pause"],
    },
    "summary_board": {
        "goal": "Close the lesson with a structured overview of the main ideas.",
        "expected_inputs": ["on_screen_text", "key_terms", "learning_goal"],
        "layout_behavior": "Top title plus a tidy grid of recap cards or concept chips.",
        "preferred_components": ["title_block", "recap_card", "label_chip"],
        "animation_patterns": ["Show the frame.", "Populate the board progressively.", "Finish by highlighting the final learning arc."],
        "pacing_rules": ["Use the board to organize memory, not re-teach everything."],
        "text_limits": "Three or four high-value anchors.",
        "emphasis_behavior": "One final highlight only.",
        "scene_types": ["summary_board"],
    },
}


def template_name_for_scene_type(scene_type: str) -> str:
    if scene_type in SCENE_TEMPLATE_LIBRARY:
        return scene_type
    return _ALIAS_TO_TEMPLATE.get(scene_type, "concept_build")


def format_scene_template_catalog_for_prompt() -> str:
    lines: list[str] = []
    for template_name, spec in SCENE_TEMPLATE_LIBRARY.items():
        scene_types = ", ".join(spec["scene_types"])
        lines.append(f"- {template_name}: {spec['goal']} Scene types: {scene_types}")
        lines.append(f"  Expected inputs: {', '.join(spec['expected_inputs'])}")
        lines.append(f"  Layout: {spec['layout_behavior']}")
        lines.append(f"  Components: {', '.join(spec['preferred_components'])}")
        for pattern in spec["animation_patterns"]:
            lines.append(f"  Motion: {pattern}")
        lines.append(f"  Text limits: {spec['text_limits']}")
        lines.append(f"  Emphasis: {spec['emphasis_behavior']}")
    return "\n".join(lines)


def build_scene_template_brief(scene: StoryboardScene) -> dict[str, Any]:
    template_name = template_name_for_scene_type(scene.scene_type)
    spec = SCENE_TEMPLATE_LIBRARY[template_name]
    return {
        "scene_id": scene.scene_id,
        "scene_type": scene.scene_type,
        "template_name": template_name,
        "template_goal": spec["goal"],
        "expected_inputs": spec["expected_inputs"],
        "layout_behavior": spec["layout_behavior"],
        "preferred_components": spec["preferred_components"],
        "preferred_animation_patterns": spec["animation_patterns"],
        "requested_layout": scene.layout_style,
        "requested_assets": [asset.asset_id for asset in scene.asset_requirements],
    }


class ExplainerScene(Scene):
    def setup(self) -> None:
        self.camera.background_color = THEME.colors.background
        super().setup()

    def beat(self, duration: float | None = None) -> None:
        self.wait(duration or THEME.motion.pause)

    def intro_badge(self, text: str, role: str = "focus"):
        badge = make_label_chip(text, role=role)
        badge.to_edge(UP + LEFT, buff=THEME.space.scene_margin)
        return badge


def _pick_lines(spec: SceneSpec, *, fallback_count: int = 3) -> list[str]:
    values = [line.strip() for line in spec.on_screen_text if line.strip()]
    if values:
        return values[:fallback_count]
    if spec.key_terms:
        return spec.key_terms[:fallback_count]
    if spec.visual_focus:
        return [spec.visual_focus]
    return [spec.learning_goal]


def _pick_question(spec: SceneSpec) -> str:
    if spec.on_screen_text:
        return spec.on_screen_text[0]
    return spec.visual_focus or spec.scene_title


def _pick_focus(spec: SceneSpec) -> str:
    return spec.visual_focus or (spec.key_terms[0] if spec.key_terms else spec.learning_goal)


def _role_for_text(spec: SceneSpec, text: str, *, default: str = "focus") -> str:
    lowered = text.lower()
    for assignment in spec.semantic_color_roles:
        target = assignment.get("target", "").lower().strip()
        if target and target in lowered:
            return assignment.get("role", default)
    return default


def _asset_or_none(spec: SceneSpec):
    if not spec.asset_requirements:
        return None
    asset = build_asset(spec.asset_requirements[0], with_label=False)
    asset.scale(0.7)
    return asset


def _make_support_nodes(spec: SceneSpec, *, default_role: str = "secondary") -> list[VGroup]:
    terms = spec.key_terms or _pick_lines(spec, fallback_count=4)
    nodes: list[VGroup] = []
    for term in terms[:4]:
        nodes.append(make_concept_node(term, role=_role_for_text(spec, term, default=default_role), width=2.5))
    return nodes


def _render_title_intro(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge(spec.pedagogical_role or "lesson")
    title = make_title_block(
        spec.scene_title,
        subtitle=spec.learning_goal,
        eyebrow=spec.scene_type.replace("_", " "),
    )
    promise = make_callout_box("What to notice", [_pick_focus(spec)], role="secondary", width=4.8)
    frame = VGroup(title, promise).arrange(DOWN, buff=0.42)
    asset = _asset_or_none(spec)
    if asset is not None:
        asset.next_to(frame, RIGHT, buff=0.6)
    scene.play(FadeIn(badge, shift=DOWN * 0.15), run_time=THEME.motion.fast)
    scene.play(Write(title), run_time=THEME.motion.slow)
    if asset is not None:
        scene.play(FadeIn(asset, shift=LEFT * 0.2), run_time=THEME.motion.medium)
    scene.play(FadeIn(promise, shift=UP * 0.2), run_time=THEME.motion.medium)
    scene.beat(THEME.motion.settle)


def _render_hook_question(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("hook", role="active_path")
    question_card = make_quiz_prompt_card(_pick_question(spec), prompt_label="Think first")
    clue_lines = _pick_lines(spec, fallback_count=2)[1:] or [spec.learning_goal]
    clue = make_callout_box("Clue", clue_lines[:1], role="focus", width=4.4)
    clue.next_to(question_card, DOWN, buff=0.42)
    scene.play(FadeIn(badge), FadeIn(question_card, shift=UP * 0.2), run_time=THEME.motion.medium)
    scene.beat(0.5)
    scene.play(FadeIn(clue, shift=UP * 0.15), Circumscribe(question_card, color=get_semantic_color("active_path")), run_time=THEME.motion.medium)
    scene.beat(THEME.motion.settle)


def _render_concept_build(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("core concept")
    hub = make_concept_node(_pick_focus(spec), role="focus", width=3.0)
    nodes = _make_support_nodes(spec)
    positions = [UP * 1.75 + LEFT * 3.3, UP * 1.7 + RIGHT * 3.1, DOWN * 1.7 + LEFT * 3.1, DOWN * 1.75 + RIGHT * 3.0]
    lines = []
    for node, pos in zip(nodes, positions):
        node.move_to(pos)
        lines.append(make_relation_line(hub.get_center(), node.get_center(), role="muted_structure"))
    scene.play(FadeIn(badge), FadeIn(hub, scale=0.9), run_time=THEME.motion.medium)
    for node, line in zip(nodes, lines):
        scene.play(Create(line), FadeIn(node, scale=0.92), run_time=THEME.motion.fast)
        scene.play(Indicate(node, color=get_semantic_color(_role_for_text(spec, node[1].text, default="secondary"))), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


def _render_concept_map(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("concept map")
    hub = make_concept_node(_pick_focus(spec), role="focus", width=2.8)
    hub.move_to(LEFT * 0.2)
    nodes = _make_support_nodes(spec, default_role="secondary")
    offsets = [UP * 2.1 + RIGHT * 3.0, UP * 0.6 + RIGHT * 3.4, DOWN * 0.9 + RIGHT * 3.25, DOWN * 2.2 + RIGHT * 2.95]
    links = []
    for node, offset in zip(nodes, offsets):
        node.move_to(offset)
        links.append(make_relation_line(hub.get_right(), node.get_left(), role="muted_structure"))
    scene.play(FadeIn(badge), FadeIn(hub, shift=UP * 0.15), run_time=THEME.motion.medium)
    scene.play(LaggedStart(*[Create(link) for link in links], lag_ratio=0.18), run_time=THEME.motion.medium)
    scene.play(LaggedStart(*[FadeIn(node, scale=0.92) for node in nodes], lag_ratio=0.15), run_time=THEME.motion.medium)
    if nodes:
        scene.play(Circumscribe(nodes[0], color=get_semantic_color(_role_for_text(spec, nodes[0][1].text, default="focus"))), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


def _render_step_by_step(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("step by step")
    steps = _pick_lines(spec, fallback_count=4)
    chips = VGroup(*[make_label_chip(f"{index + 1}. {step}", role="focus" if index == 0 else "muted_structure") for index, step in enumerate(steps)])
    chips.arrange(DOWN, buff=0.24, aligned_edge=LEFT).to_edge(LEFT, buff=THEME.space.scene_margin + 0.3)
    focus_panel = make_callout_box("Current step", [steps[0]], role="focus", width=4.6)
    focus_panel.to_edge(RIGHT, buff=THEME.space.scene_margin + 0.4)
    scene.play(FadeIn(badge), LaggedStart(*[FadeIn(chip, shift=RIGHT * 0.12) for chip in chips], lag_ratio=0.12), run_time=THEME.motion.medium)
    scene.play(FadeIn(focus_panel, shift=LEFT * 0.18), run_time=THEME.motion.medium)
    for index, step in enumerate(steps[1:], start=1):
        next_panel = make_callout_box("Current step", [step], role="focus", width=4.6)
        next_panel.move_to(focus_panel)
        scene.play(
            FadeToColor(chips[index - 1], THEME.colors.text_secondary),
            FadeToColor(chips[index], get_semantic_color("focus")),
            ReplacementTransform(focus_panel, next_panel),
            run_time=THEME.motion.fast,
        )
        focus_panel = next_panel
    scene.beat(THEME.motion.settle)


def _render_process_flow(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("process flow", role="active_path")
    stages = _pick_lines(spec, fallback_count=4)
    boxes = VGroup(*[make_process_box(stage, role="focus" if index == 0 else "muted_structure") for index, stage in enumerate(stages)]).arrange(RIGHT, buff=0.55)
    boxes.scale(0.88)
    arrows = VGroup(*[make_connector(boxes[index], boxes[index + 1], role="active_path") for index in range(len(boxes) - 1)])
    asset = _asset_or_none(spec)
    if asset is not None:
        asset.next_to(boxes, UP, buff=0.55)
    scene.play(FadeIn(badge), FadeIn(boxes[0], shift=UP * 0.12), run_time=THEME.motion.medium)
    if asset is not None:
        scene.play(FadeIn(asset), run_time=THEME.motion.fast)
    for index in range(1, len(boxes)):
        scene.play(Create(arrows[index - 1][0] if isinstance(arrows[index - 1], VGroup) else arrows[index - 1]), FadeIn(boxes[index], shift=UP * 0.12), run_time=THEME.motion.fast)
        scene.play(Indicate(boxes[index], color=get_semantic_color("active_path")), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


def _render_worked_example(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("worked example", role="success")
    parts = _pick_lines(spec, fallback_count=3)
    while len(parts) < 3:
        parts.append(spec.learning_goal)
    panels = VGroup(
        make_callout_box("Input", [parts[0]], role="secondary", width=3.2),
        make_callout_box("Transform", [parts[1]], role="focus", width=3.2),
        make_callout_box("Output", [parts[2]], role="success", width=3.2),
    ).arrange(RIGHT, buff=0.45)
    connectors = VGroup(
        make_connector(panels[0], panels[1], role="active_path"),
        make_connector(panels[1], panels[2], role="success"),
    )
    banner = make_remember_banner(spec.learning_goal)
    banner.next_to(panels, DOWN, buff=0.5)
    scene.play(FadeIn(badge), FadeIn(panels[0], shift=RIGHT * 0.16), run_time=THEME.motion.medium)
    scene.play(Create(connectors[0][0] if isinstance(connectors[0], VGroup) else connectors[0]), FadeIn(panels[1], shift=RIGHT * 0.16), run_time=THEME.motion.fast)
    scene.play(Create(connectors[1][0] if isinstance(connectors[1], VGroup) else connectors[1]), FadeIn(panels[2], shift=RIGHT * 0.16), run_time=THEME.motion.fast)
    scene.play(FadeIn(banner, shift=UP * 0.1), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


def _render_state_transition(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("state transition", role="warning")
    states = spec.key_terms[:3] or _pick_lines(spec, fallback_count=3)
    while len(states) < 3:
        states.append(f"State {len(states) + 1}")
    boxes = VGroup(
        make_state_box(states[0], role="focus"),
        make_state_box(states[1], role="active_path"),
        make_state_box(states[2], role="success"),
    ).arrange(RIGHT, buff=1.0)
    valid_1 = make_connector(boxes[0], boxes[1], role="active_path", label="valid")
    valid_2 = make_connector(boxes[1], boxes[2], role="success", label="valid")
    invalid = make_relation_line(boxes[0].get_top(), boxes[2].get_top(), role="warning", dashed=True)
    invalid_label = make_warning_badge("invalid")
    invalid_label.next_to(invalid, UP, buff=0.12)
    scene.play(FadeIn(badge), LaggedStart(*[FadeIn(box, shift=UP * 0.12) for box in boxes], lag_ratio=0.16), run_time=THEME.motion.medium)
    scene.play(Create(valid_1[0]), FadeIn(valid_1[1]), run_time=THEME.motion.fast)
    scene.play(Create(valid_2[0]), FadeIn(valid_2[1]), run_time=THEME.motion.fast)
    scene.play(Create(invalid), FadeIn(invalid_label, shift=UP * 0.1), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


def _render_code_walkthrough(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("code walkthrough")
    lines = _pick_lines(spec, fallback_count=6)
    code_lines = lines[: min(6, len(lines))]
    code_panel = make_code_panel(code_lines, active_line=0, width=5.8)
    note_panel = make_callout_box("What to notice", [spec.visual_focus or spec.learning_goal], role="focus", width=3.6)
    layout = VGroup(code_panel, note_panel).arrange(RIGHT, buff=0.5)
    scene.play(FadeIn(badge), FadeIn(code_panel, shift=UP * 0.12), run_time=THEME.motion.medium)
    scene.play(FadeIn(note_panel, shift=LEFT * 0.15), run_time=THEME.motion.fast)
    for index in range(1, min(len(code_lines), 4)):
        next_panel = make_code_panel(code_lines, active_line=index, width=5.8)
        next_panel.move_to(code_panel)
        scene.play(TransformMatchingShapes(code_panel, next_panel), run_time=THEME.motion.fast)
        code_panel = next_panel
    scene.beat(THEME.motion.settle)


def _render_comparison(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("comparison", role="secondary")
    points = _pick_lines(spec, fallback_count=4)
    left_points = points[:2] or [spec.learning_goal]
    right_points = points[2:4] or [spec.visual_focus or spec.learning_goal]
    left = make_comparison_column("Option A", left_points, role="focus")
    right = make_comparison_column("Option B", right_points, role="secondary")
    banner = make_remember_banner(spec.visual_focus or spec.learning_goal)
    columns = VGroup(left, right).arrange(RIGHT, buff=0.48)
    banner.next_to(columns, DOWN, buff=0.45)
    scene.play(FadeIn(badge), FadeIn(left, shift=RIGHT * 0.16), FadeIn(right, shift=LEFT * 0.16), run_time=THEME.motion.medium)
    scene.play(Circumscribe(left if spec.emphasis_targets else right, color=get_semantic_color("focus")), run_time=THEME.motion.fast)
    scene.play(FadeIn(banner, shift=UP * 0.1), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


def _render_recap_card(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("recap", role="success")
    takeaways = _pick_lines(spec, fallback_count=4)
    recap = make_recap_card(spec.scene_title, takeaways[:4], role="success")
    banner = make_remember_banner(spec.learning_goal)
    banner.next_to(recap, DOWN, buff=0.42)
    scene.play(FadeIn(badge), FadeIn(recap, shift=UP * 0.15), run_time=THEME.motion.medium)
    scene.play(FadeIn(banner, shift=UP * 0.1), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


def _render_quiz_pause(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("quiz pause", role="active_path")
    question = make_quiz_prompt_card(_pick_question(spec))
    answer_lines = _pick_lines(spec, fallback_count=2)[1:] or [spec.learning_goal]
    answer = make_callout_box("Reveal", answer_lines[:1], role="success", width=4.3)
    answer.next_to(question, DOWN, buff=0.5)
    scene.play(FadeIn(badge), FadeIn(question, scale=0.95), run_time=THEME.motion.medium)
    scene.beat(0.7)
    scene.play(FadeIn(answer, shift=UP * 0.15), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


def _render_summary_board(scene: ExplainerScene, spec: SceneSpec) -> None:
    badge = scene.intro_badge("summary", role="success")
    title = make_title_block(spec.scene_title, subtitle=spec.learning_goal, eyebrow="summary")
    title.to_edge(UP, buff=THEME.space.scene_margin + 0.25)
    cards = _pick_lines(spec, fallback_count=4)
    recap_cards = VGroup(
        *[
            make_recap_card(f"Takeaway {index + 1}", [line], role="focus" if index == 0 else "secondary", width=3.2)
            for index, line in enumerate(cards[:4])
        ]
    )
    recap_cards.arrange_in_grid(rows=2 if len(recap_cards) > 2 else 1, cols=2 if len(recap_cards) > 1 else 1, buff=(0.35, 0.35))
    recap_cards.next_to(title, DOWN, buff=0.55)
    scene.play(FadeIn(badge), Write(title), run_time=THEME.motion.medium)
    scene.play(LaggedStart(*[FadeIn(card, shift=UP * 0.12) for card in recap_cards], lag_ratio=0.14), run_time=THEME.motion.medium)
    if len(recap_cards) > 0:
        scene.play(Circumscribe(recap_cards[0], color=get_semantic_color("success")), run_time=THEME.motion.fast)
    scene.beat(THEME.motion.settle)


_RENDERERS = {
    "title_intro": _render_title_intro,
    "hook_question": _render_hook_question,
    "concept_build": _render_concept_build,
    "concept_map": _render_concept_map,
    "step_by_step_reveal": _render_step_by_step,
    "process_flow": _render_process_flow,
    "worked_example": _render_worked_example,
    "state_transition": _render_state_transition,
    "code_walkthrough": _render_code_walkthrough,
    "comparison": _render_comparison,
    "recap_card": _render_recap_card,
    "quiz_pause": _render_quiz_pause,
    "summary_board": _render_summary_board,
}


def render_storyboard_scene(scene: ExplainerScene, spec: SceneSpec) -> None:
    template_name = template_name_for_scene_type(spec.scene_type)
    renderer = _RENDERERS[template_name]
    renderer(scene, spec)


def builder_shared_notes() -> list[str]:
    return [
        *theme_design_notes(),
        "Templates are rendered by visuals.scene_templates via deterministic scene-type dispatch.",
        "Components come from visuals.components and optional primitive assets from visuals.assets.",
    ]
