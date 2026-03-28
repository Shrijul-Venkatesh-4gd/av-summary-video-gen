from __future__ import annotations

from models.storyboard import Storyboard
from models.validation import StoryboardValidationReport, ValidationIssue
from utils.assets import ASSET_CATALOG


ATTENTION_RESET_SCENE_TYPES = {"hook_question", "quiz_pause", "recap_card", "summary_board"}


def validate_storyboard(storyboard: Storyboard) -> StoryboardValidationReport:
    issues: list[ValidationIssue] = []
    seen_reset_gap = 0
    type_streak = 1
    layout_streak = 1
    unique_scene_types = {scene.scene_type for scene in storyboard.scenes}

    previous_scene = None
    previous_transition = None
    transition_repeat_count = 1

    for scene in storyboard.scenes:
        if not scene.learning_goal.strip():
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="missing_learning_goal",
                    message="Every storyboard scene must include a learning_goal.",
                    scene_id=scene.scene_id,
                    field_name="learning_goal",
                )
            )
        if not scene.pedagogical_role.strip():
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="missing_pedagogical_role",
                    message="Every storyboard scene must include a pedagogical_role.",
                    scene_id=scene.scene_id,
                    field_name="pedagogical_role",
                )
            )

        word_count = sum(len(line.split()) for line in scene.on_screen_text)
        if word_count > 36:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="too_much_on_screen_text",
                    message="On-screen text is too dense for one scene. Keep text short and scannable.",
                    scene_id=scene.scene_id,
                    field_name="on_screen_text",
                )
            )
        elif word_count > 24:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="heavy_on_screen_text",
                    message="On-screen text is getting dense. Let narration carry more of the explanation.",
                    scene_id=scene.scene_id,
                    field_name="on_screen_text",
                )
            )

        if scene.estimated_duration_sec >= 45 and len(scene.animation_plan) < 2:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="low_visual_change",
                    message="Long scene with very little visual change. Add more progression or split the scene.",
                    scene_id=scene.scene_id,
                    field_name="animation_plan",
                )
            )
        if scene.estimated_duration_sec >= 60 and len(scene.animation_plan) < 2:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="static_scene_too_long",
                    message="Scene duration is too long for such a static animation plan.",
                    scene_id=scene.scene_id,
                    field_name="animation_plan",
                )
            )

        for asset in scene.asset_requirements:
            if asset.asset_id not in ASSET_CATALOG:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="unknown_asset_request",
                        message=f"Asset '{asset.asset_id}' is not in the reusable asset catalog.",
                        scene_id=scene.scene_id,
                        field_name="asset_requirements",
                    )
                )

        if previous_scene is not None:
            if scene.scene_type == previous_scene.scene_type:
                type_streak += 1
                if type_streak >= 2 and not scene.variation_justification:
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            code="repeated_scene_type",
                            message="Consecutive scenes repeat the same scene_type without a justification.",
                            scene_id=scene.scene_id,
                            field_name="scene_type",
                        )
                    )
                if type_streak >= 3:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="scene_type_streak",
                            message="Too many scenes repeat the same scene_type in a row.",
                            scene_id=scene.scene_id,
                            field_name="scene_type",
                        )
                    )
            else:
                type_streak = 1

            if scene.layout_style == previous_scene.layout_style:
                layout_streak += 1
                if layout_streak >= 2 and not scene.variation_justification:
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            code="repeated_layout_style",
                            message="Consecutive scenes repeat the same layout_style without a justification.",
                            scene_id=scene.scene_id,
                            field_name="layout_style",
                        )
                    )
                if layout_streak >= 3:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="layout_style_streak",
                            message="Too many scenes repeat the same layout_style in a row.",
                            scene_id=scene.scene_id,
                            field_name="layout_style",
                        )
                    )
            else:
                layout_streak = 1

        if scene.transition_style == previous_transition:
            transition_repeat_count += 1
            if transition_repeat_count >= 3:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="repeated_transition_style",
                        message="The same transition style appears many times in a row.",
                        scene_id=scene.scene_id,
                        field_name="transition_style",
                    )
                )
        else:
            transition_repeat_count = 1

        seen_reset_gap += scene.estimated_duration_sec
        if scene.attention_reset or scene.scene_type in ATTENTION_RESET_SCENE_TYPES:
            seen_reset_gap = 0
        elif seen_reset_gap > 30:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="attention_reset_gap",
                    message="Add an attention reset within roughly every 20 to 30 seconds.",
                    scene_id=scene.scene_id,
                )
            )
            seen_reset_gap = 0

        previous_scene = scene
        previous_transition = scene.transition_style

    if len(storyboard.scenes) >= 4 and len(unique_scene_types) < 3:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="low_scene_type_diversity",
                message="Storyboard could use more pedagogical variety across scene types.",
            )
        )

    if not any(scene.scene_type == "worked_example" for scene in storyboard.scenes):
        issues.append(
            ValidationIssue(
                severity="warning",
                code="missing_worked_example",
                message="Consider adding a worked_example scene so students see the idea in action.",
            )
        )

    if not any(scene.scene_type in {"hook_question", "quiz_pause"} for scene in storyboard.scenes):
        issues.append(
            ValidationIssue(
                severity="warning",
                code="missing_question_driven_scene",
                message="Consider adding a question-driven scene to reset attention and deepen learning.",
            )
        )

    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    return StoryboardValidationReport(
        valid=error_count == 0,
        warning_count=warning_count,
        error_count=error_count,
        issues=issues,
    )
