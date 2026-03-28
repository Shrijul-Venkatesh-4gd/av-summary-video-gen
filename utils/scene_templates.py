from __future__ import annotations

from typing import Any

from models.storyboard import StoryboardScene


SCENE_TEMPLATE_LIBRARY: dict[str, dict[str, Any]] = {
    "hook_question": {
        "goal": "Open with curiosity and a visible problem to solve.",
        "animation_patterns": [
            "Show a bold question first with generous whitespace.",
            "Pause briefly before revealing a clue or contrast.",
            "Use one highlight or motion cue to steer attention to the key unknown.",
        ],
        "preferred_layouts": [
            "center_question_with_footer_clue",
            "split_question_and_visual_hint",
        ],
    },
    "concept_map": {
        "goal": "Reveal how one core idea branches into related pieces.",
        "animation_patterns": [
            "Start with a central concept node.",
            "Grow branches one by one, not all at once.",
            "Highlight only the branch being explained right now.",
        ],
        "preferred_layouts": [
            "radial_map",
            "center_node_with_side_branches",
        ],
    },
    "step_by_step_reveal": {
        "goal": "Teach a sequence clearly with one step active at a time.",
        "animation_patterns": [
            "Show the current numbered step prominently.",
            "Dim previous steps instead of removing all context.",
            "Use arrows or separators to mark progression.",
        ],
        "preferred_layouts": [
            "vertical_steps",
            "left_steps_right_focus",
        ],
    },
    "worked_example": {
        "goal": "Walk through an example from input to reasoning to result.",
        "animation_patterns": [
            "Present the example input first.",
            "Animate the process in stages using boxes, arrows, or annotations.",
            "End with the output and a short takeaway.",
        ],
        "preferred_layouts": [
            "input_process_output",
            "example_panel_with_callouts",
        ],
    },
    "state_transition": {
        "goal": "Show how a system changes state and what transitions are valid or invalid.",
        "animation_patterns": [
            "Place states with clear spatial separation.",
            "Animate arrows along valid paths.",
            "Use warning styling for invalid or mistaken transitions.",
        ],
        "preferred_layouts": [
            "horizontal_state_chain",
            "triangle_state_graph",
        ],
    },
    "code_demo": {
        "goal": "Teach code in chunks instead of a full wall of text.",
        "animation_patterns": [
            "Reveal code a few lines at a time.",
            "Highlight the active line or token during explanation.",
            "Show output or result beside the code when useful.",
        ],
        "preferred_layouts": [
            "left_code_right_output",
            "top_code_bottom_explanation",
        ],
    },
    "recap_card": {
        "goal": "Compress a recent idea into a few memorable takeaways.",
        "animation_patterns": [
            "Show no more than three short points.",
            "Reveal takeaways one at a time with emphasis.",
            "Finish on the strongest phrase or memory cue.",
        ],
        "preferred_layouts": [
            "three_takeaways",
            "center_phrase_with_side_notes",
        ],
    },
    "quiz_pause": {
        "goal": "Reset attention by asking the learner to predict before the answer appears.",
        "animation_patterns": [
            "Show the question with visual pause space.",
            "Hold the prompt before revealing the answer.",
            "Use a clear answer reveal instead of a sudden text dump.",
        ],
        "preferred_layouts": [
            "prompt_then_answer",
            "split_prediction_reveal",
        ],
    },
}


def format_scene_template_catalog_for_prompt() -> str:
    lines: list[str] = []
    for scene_type, spec in SCENE_TEMPLATE_LIBRARY.items():
        lines.append(f"- {scene_type}: {spec['goal']}")
        lines.extend(
            f"  Pattern: {pattern}" for pattern in spec["animation_patterns"]
        )
        lines.append(
            f"  Preferred layouts: {', '.join(spec['preferred_layouts'])}"
        )
    return "\n".join(lines)


def build_scene_template_brief(scene: StoryboardScene) -> dict[str, Any]:
    spec = SCENE_TEMPLATE_LIBRARY.get(scene.scene_type, {})
    return {
        "scene_id": scene.scene_id,
        "scene_type": scene.scene_type,
        "template_goal": spec.get("goal", "Teach the scene clearly with purposeful motion."),
        "preferred_layouts": spec.get("preferred_layouts", [scene.layout_style]),
        "preferred_animation_patterns": spec.get(
            "animation_patterns",
            ["Use progressive reveal and highlight only the active idea."],
        ),
        "requested_layout": scene.layout_style,
        "requested_assets": [asset.asset_id for asset in scene.asset_requirements],
    }
