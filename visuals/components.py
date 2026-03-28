from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    CurvedArrow,
    DashedLine,
    Group,
    Line,
    Paragraph,
    Rectangle,
    RoundedRectangle,
    SurroundingRectangle,
    Text,
    VGroup,
)

from visuals.theme import THEME, get_semantic_color


def body_text(text: str, *, scale: float | None = None, color: str | None = None) -> Text:
    return Text(
        text,
        font=THEME.type.body_font,
        color=color or THEME.colors.text_primary,
        font_size=int(100 * (scale or THEME.type.body_md)),
    )


def label_text(text: str, *, color: str | None = None) -> Text:
    return Text(
        text,
        font=THEME.type.body_font,
        color=color or THEME.colors.text_secondary,
        font_size=int(100 * THEME.type.label_xs),
    )


def monospace_text(text: str, *, color: str | None = None, scale: float | None = None) -> Text:
    return Text(
        text,
        font=THEME.type.mono_font,
        color=color or THEME.colors.text_primary,
        font_size=int(100 * (scale or THEME.type.body_sm)),
    )


def make_title_block(
    title: str,
    *,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    align: str = "center",
) -> VGroup:
    items = []
    if eyebrow:
        items.append(label_text(eyebrow.upper(), color=get_semantic_color("focus")))
    items.append(
        Text(
            title,
            font=THEME.type.title_font,
            color=THEME.colors.text_primary,
            font_size=int(100 * THEME.type.display_lg),
            weight="BOLD",
        )
    )
    if subtitle:
        items.append(
            Text(
                subtitle,
                font=THEME.type.body_font,
                color=THEME.colors.text_secondary,
                font_size=int(100 * THEME.type.body_md),
            )
        )
    block = VGroup(*items).arrange(DOWN, buff=THEME.space.card_gap)
    if align == "left":
        for item in block:
            item.align_to(block, LEFT)
    return block


def make_label_chip(text: str, *, role: str = "focus") -> VGroup:
    content = label_text(text, color=get_semantic_color(role, fallback="focus"))
    box = RoundedRectangle(
        width=content.width + 0.34,
        height=content.height + 0.22,
        corner_radius=0.16,
        fill_color=THEME.colors.panel_alt,
        fill_opacity=1,
        stroke_color=get_semantic_color(role, fallback="focus"),
        stroke_width=THEME.stroke.medium,
    )
    content.move_to(box.get_center())
    return VGroup(box, content)


def make_callout_box(
    title: str,
    lines: list[str],
    *,
    role: str = "secondary",
    width: float = 4.4,
) -> VGroup:
    heading = label_text(title.upper(), color=get_semantic_color(role, fallback="secondary"))
    body = Paragraph(
        *lines,
        alignment="left",
        font=THEME.type.body_font,
        color=THEME.colors.text_primary,
        line_spacing=0.75,
        font_size=int(100 * THEME.type.body_sm),
    )
    body.set_width(min(width - 0.4, body.width))
    stack = VGroup(heading, body).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
    panel = RoundedRectangle(
        width=max(width, stack.width + 0.42),
        height=stack.height + 0.42,
        corner_radius=THEME.space.corner_radius,
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=get_semantic_color(role, fallback="secondary"),
        stroke_width=THEME.stroke.medium,
    )
    stack.move_to(panel.get_center())
    return VGroup(panel, stack)


def make_concept_node(label: str, *, role: str = "focus", width: float = 2.6) -> VGroup:
    text = body_text(label, scale=THEME.type.body_sm)
    text.set_width(min(width - 0.34, max(1.1, text.width)))
    box = RoundedRectangle(
        width=max(width, text.width + 0.36),
        height=max(0.86, text.height + 0.26),
        corner_radius=0.2,
        fill_color=THEME.colors.panel_alt,
        fill_opacity=1,
        stroke_color=get_semantic_color(role, fallback="focus"),
        stroke_width=THEME.stroke.medium,
    )
    text.move_to(box.get_center())
    return VGroup(box, text)


def make_process_box(label: str, *, caption: str | None = None, role: str = "muted_structure") -> VGroup:
    title = body_text(label, scale=THEME.type.body_sm)
    items = [title]
    if caption:
        items.append(label_text(caption))
    stack = VGroup(*items).arrange(DOWN, buff=0.14)
    box = RoundedRectangle(
        width=max(2.25, stack.width + 0.5),
        height=max(1.0, stack.height + 0.38),
        corner_radius=0.18,
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=get_semantic_color(role, fallback="muted_structure"),
        stroke_width=THEME.stroke.medium,
    )
    stack.move_to(box.get_center())
    return VGroup(box, stack)


def make_state_box(label: str, *, role: str = "muted_structure", detail: str | None = None) -> VGroup:
    title = body_text(label, scale=THEME.type.body_sm)
    items = [title]
    if detail:
        items.append(label_text(detail))
    stack = VGroup(*items).arrange(DOWN, buff=0.12)
    box = RoundedRectangle(
        width=max(2.0, stack.width + 0.42),
        height=max(0.94, stack.height + 0.34),
        corner_radius=0.18,
        fill_color=THEME.colors.panel_alt,
        fill_opacity=1,
        stroke_color=get_semantic_color(role, fallback="muted_structure"),
        stroke_width=THEME.stroke.medium,
    )
    stack.move_to(box.get_center())
    return VGroup(box, stack)


def make_comparison_column(title: str, points: list[str], *, role: str = "secondary", width: float = 3.4) -> VGroup:
    heading = make_label_chip(title, role=role)
    body = Paragraph(
        *points,
        alignment="left",
        font=THEME.type.body_font,
        color=THEME.colors.text_primary,
        line_spacing=0.82,
        font_size=int(100 * THEME.type.body_sm),
    )
    body.set_width(min(width - 0.4, body.width))
    stack = VGroup(heading, body).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
    box = RoundedRectangle(
        width=max(width, stack.width + 0.44),
        height=stack.height + 0.44,
        corner_radius=THEME.space.corner_radius,
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=get_semantic_color(role, fallback="secondary"),
        stroke_width=THEME.stroke.medium,
    )
    stack.move_to(box.get_center())
    return VGroup(box, stack)


def make_recap_card(title: str, takeaways: list[str], *, role: str = "success", width: float = 4.2) -> VGroup:
    heading = make_label_chip(title, role=role)
    rows = VGroup(
        *[
            body_text(point, scale=THEME.type.body_sm, color=THEME.colors.text_primary)
            for point in takeaways
        ]
    ).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
    rows.set_width(min(width - 0.44, rows.width))
    stack = VGroup(heading, rows).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
    panel = RoundedRectangle(
        width=max(width, stack.width + 0.5),
        height=stack.height + 0.48,
        corner_radius=THEME.space.corner_radius,
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=get_semantic_color(role, fallback="success"),
        stroke_width=THEME.stroke.medium,
    )
    stack.move_to(panel.get_center())
    return VGroup(panel, stack)


def make_code_panel(
    code_lines: list[str],
    *,
    title: str = "Code Walkthrough",
    active_line: int | None = None,
    width: float = 5.8,
) -> VGroup:
    heading = make_label_chip(title, role="focus")
    code_group = VGroup(
        *[monospace_text(line, scale=0.3) for line in code_lines]
    ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    code_group.set_width(min(width - 0.55, code_group.width))
    panel = RoundedRectangle(
        width=max(width, code_group.width + 0.54),
        height=code_group.height + heading.height + 0.72,
        corner_radius=THEME.space.corner_radius,
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=THEME.colors.outline,
        stroke_width=THEME.stroke.medium,
    )
    heading.next_to(panel.get_top(), DOWN, buff=0.18)
    heading.align_to(panel, LEFT).shift(RIGHT * 0.24)
    code_group.next_to(heading, DOWN, buff=0.24)
    code_group.align_to(heading, LEFT)
    items = [panel, heading, code_group]
    if active_line is not None and 0 <= active_line < len(code_group):
        highlight = SurroundingRectangle(
            code_group[active_line],
            buff=0.08,
            color=get_semantic_color("active_path"),
            stroke_width=THEME.stroke.medium,
        )
        items.append(highlight)
    return VGroup(*items)


def make_warning_badge(text: str = "Watch out") -> VGroup:
    return make_label_chip(text, role="warning")


def make_remember_banner(text: str) -> VGroup:
    label = Text(
        text,
        font=THEME.type.body_font,
        color=THEME.colors.text_primary,
        font_size=int(100 * THEME.type.body_sm),
        weight="BOLD",
    )
    banner = RoundedRectangle(
        width=label.width + 0.48,
        height=label.height + 0.26,
        corner_radius=0.18,
        fill_color=THEME.colors.panel_alt,
        fill_opacity=1,
        stroke_color=get_semantic_color("active_path"),
        stroke_width=THEME.stroke.medium,
    )
    label.move_to(banner.get_center())
    return VGroup(banner, label)


def make_quiz_prompt_card(question: str, *, prompt_label: str = "Pause and predict") -> VGroup:
    prompt = make_label_chip(prompt_label, role="active_path")
    question_text = Text(
        question,
        font=THEME.type.title_font,
        color=THEME.colors.text_primary,
        font_size=int(100 * THEME.type.heading_md),
        weight="BOLD",
    )
    question_text.set_width(min(7.2, question_text.width))
    card = RoundedRectangle(
        width=max(7.6, question_text.width + 0.6),
        height=question_text.height + prompt.height + 0.8,
        corner_radius=0.28,
        fill_color=THEME.colors.panel,
        fill_opacity=1,
        stroke_color=get_semantic_color("active_path"),
        stroke_width=THEME.stroke.medium,
    )
    prompt.next_to(card.get_top(), DOWN, buff=0.22)
    question_text.next_to(prompt, DOWN, buff=0.26)
    question_text.align_to(card, LEFT).shift(RIGHT * 0.32)
    prompt.align_to(card, LEFT).shift(RIGHT * 0.32)
    return VGroup(card, prompt, question_text)


def make_connector(start, end, *, role: str = "active_path", label: str | None = None, curved: bool = False):
    if curved:
        arrow = CurvedArrow(
            start.get_center(),
            end.get_center(),
            color=get_semantic_color(role, fallback="active_path"),
            stroke_width=THEME.stroke.medium,
        )
    else:
        arrow = Arrow(
            start.get_edge_center(RIGHT),
            end.get_edge_center(LEFT),
            buff=0.1,
            color=get_semantic_color(role, fallback="active_path"),
            stroke_width=THEME.stroke.medium,
        )
    if label is None:
        return arrow
    text = label_text(label, color=get_semantic_color(role, fallback="active_path"))
    text.next_to(arrow, UP, buff=0.08)
    return VGroup(arrow, text)


def make_relation_line(start_point, end_point, *, role: str = "muted_structure", dashed: bool = False):
    line_cls = DashedLine if dashed else Line
    return line_cls(
        start_point,
        end_point,
        color=get_semantic_color(role, fallback="muted_structure"),
        stroke_width=THEME.stroke.medium,
    )


def make_focus_outline(target, *, role: str = "focus"):
    return SurroundingRectangle(
        target,
        buff=0.12,
        color=get_semantic_color(role, fallback="focus"),
        stroke_width=THEME.stroke.medium,
        corner_radius=0.18,
    )


def pair_with_panel(content: Group, *, role: str = "muted_structure", padding: float = 0.22) -> VGroup:
    panel = SurroundingRectangle(
        content,
        buff=padding,
        color=get_semantic_color(role, fallback="muted_structure"),
        stroke_width=THEME.stroke.medium,
        corner_radius=THEME.space.corner_radius,
    )
    panel.set_fill(THEME.colors.panel, opacity=0.92)
    return VGroup(panel, content)
