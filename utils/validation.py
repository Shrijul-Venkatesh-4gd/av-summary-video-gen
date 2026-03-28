from __future__ import annotations

from models.storyboard import Storyboard
from models.validation import StoryboardValidationReport, ValidationIssue
from utils.assets import ASSET_CATALOG
from utils.budgeting import count_words
from utils.settings import (
    MAX_ON_SCREEN_WORDS_PER_SCENE,
    MAX_SCENE_NARRATION_WORDS,
    MAX_STORYBOARD_SCENES,
    MAX_TOTAL_LESSON_DURATION_SEC,
)


ATTENTION_RESET_SCENE_TYPES = {"hook_question", "quiz_pause", "recap_card", "summary_board"}
ACCENT_ROLES = {"focus", "secondary", "active_path", "warning", "success"}


def _looks_like_text_slide(scene) -> bool:
    lowered_layout = scene.layout_style.lower()
    lowered_strategy = scene.visual_strategy.lower()
    text_slide_prone_types = {
        "title_card",
        "title_intro",
        "hook_question",
        "comparison",
        "recap_card",
        "summary_board",
    }
    return (
        "bullet" in lowered_layout
        or "list" in lowered_layout
        or "bullet" in lowered_strategy
        or "list" in lowered_strategy
        or len(scene.on_screen_text) >= 5
        or (scene.scene_type in text_slide_prone_types and len(scene.on_screen_text) >= 4)
    )


def validate_storyboard(storyboard: Storyboard) -> StoryboardValidationReport:
    issues: list[ValidationIssue] = []
    seen_reset_gap = 0
    type_streak = 1
    layout_streak = 1
    unique_scene_types = {scene.scene_type for scene in storyboard.scenes}
    inferred_total_duration = sum(scene.estimated_duration_sec for scene in storyboard.scenes)

    if len(storyboard.scenes) > MAX_STORYBOARD_SCENES:
        issues.append(
            ValidationIssue(
                severity="error",
                code="too_many_scenes",
                message=f"Storyboard exceeds the configured scene limit of {MAX_STORYBOARD_SCENES}.",
            )
        )
    if storyboard.total_estimated_duration_sec > MAX_TOTAL_LESSON_DURATION_SEC:
        issues.append(
            ValidationIssue(
                severity="error",
                code="lesson_duration_limit_exceeded",
                message=(
                    "Storyboard total duration exceeds the configured lesson duration "
                    f"limit of {MAX_TOTAL_LESSON_DURATION_SEC} seconds."
                ),
            )
        )
    if inferred_total_duration > MAX_TOTAL_LESSON_DURATION_SEC:
        issues.append(
            ValidationIssue(
                severity="error",
                code="scene_duration_limit_exceeded",
                message=(
                    "Combined scene durations exceed the configured lesson duration "
                    f"limit of {MAX_TOTAL_LESSON_DURATION_SEC} seconds."
                ),
            )
        )

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
        if not scene.visual_focus.strip():
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="missing_visual_focus",
                    message="Every storyboard scene must include a clear visual_focus.",
                    scene_id=scene.scene_id,
                    field_name="visual_focus",
                )
            )
        if not scene.semantic_color_roles:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="missing_semantic_color_roles",
                    message="Every storyboard scene must assign at least one semantic color role.",
                    scene_id=scene.scene_id,
                    field_name="semantic_color_roles",
                )
            )
        else:
            seen_targets: dict[str, str] = {}
            accent_roles = {
                assignment.role
                for assignment in scene.semantic_color_roles
                if assignment.role in ACCENT_ROLES
            }
            for assignment in scene.semantic_color_roles:
                key = assignment.target.strip().lower()
                if not key:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="empty_semantic_color_target",
                            message="Semantic color assignments need a non-empty target.",
                            scene_id=scene.scene_id,
                            field_name="semantic_color_roles",
                        )
                    )
                    continue
                previous_role = seen_targets.get(key)
                if previous_role is not None and previous_role != assignment.role:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="conflicting_semantic_color_role",
                            message=(
                                f"Target '{assignment.target}' is assigned multiple semantic color roles "
                                "within the same scene."
                            ),
                            scene_id=scene.scene_id,
                            field_name="semantic_color_roles",
                        )
                    )
                else:
                    seen_targets[key] = assignment.role
            if len(accent_roles) > 3:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="too_many_accent_roles",
                        message="Scene uses too many accent color roles. Keep emphasis to one or two accents when possible.",
                        scene_id=scene.scene_id,
                        field_name="semantic_color_roles",
                    )
                )

        narration_word_count = count_words(scene.narration_text)
        if narration_word_count > MAX_SCENE_NARRATION_WORDS:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="narration_too_long",
                    message=(
                        "Narration is too long for one scene. Keep narration within "
                        f"{MAX_SCENE_NARRATION_WORDS} words."
                    ),
                    scene_id=scene.scene_id,
                    field_name="narration_text",
                )
            )

        word_count = sum(count_words(line) for line in scene.on_screen_text)
        if word_count > MAX_ON_SCREEN_WORDS_PER_SCENE:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="too_much_on_screen_text",
                    message=(
                        "On-screen text is too dense for one scene. Keep text within "
                        f"{MAX_ON_SCREEN_WORDS_PER_SCENE} words."
                    ),
                    scene_id=scene.scene_id,
                    field_name="on_screen_text",
                )
            )
        elif word_count > max(8, MAX_ON_SCREEN_WORDS_PER_SCENE - 4):
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="heavy_on_screen_text",
                    message="On-screen text is getting dense. Let narration carry more of the explanation.",
                    scene_id=scene.scene_id,
                    field_name="on_screen_text",
                )
            )
        if _looks_like_text_slide(scene):
            severity = "warning"
            code = "generic_text_slide_fallback"
            message = (
                "Scene is drifting toward a generic text-slide layout. Prefer a stronger diagram, flow, contrast, or concept-focused structure."
            )
            if scene.scene_type in {"title_card", "title_intro", "recap_card", "summary_board"} and len(scene.on_screen_text) >= 5:
                severity = "error"
                code = "text_slide_overuse"
                message = "Scene looks like a dense title-and-bullets fallback. Reduce text and strengthen the visual strategy."
            issues.append(
                ValidationIssue(
                    severity=severity,
                    code=code,
                    message=message,
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
