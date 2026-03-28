from __future__ import annotations

import json
from math import ceil
import re
from typing import Any

from pydantic import BaseModel

from utils.settings import APPROX_CHARS_PER_TOKEN


def serialize_for_budget(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, BaseModel):
        return payload.model_dump_json(indent=2, exclude_none=True)
    return json.dumps(payload, indent=2, ensure_ascii=False, default=str)


def estimate_tokens(payload: Any) -> int:
    text = serialize_for_budget(payload)
    if not text:
        return 0
    chars_per_token = max(APPROX_CHARS_PER_TOKEN, 1)
    return max(1, ceil(len(text) / chars_per_token))


def estimate_characters(payload: Any) -> int:
    return len(serialize_for_budget(payload))


def count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def truncate_words(text: str, max_words: int) -> str:
    words = re.findall(r"\S+", text)
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).strip()


def ensure_within_budget(
    *,
    stage_name: str,
    payload: Any,
    max_tokens: int,
    max_characters: int | None = None,
    budget_label: str = "stage input",
) -> tuple[int, int]:
    token_estimate = estimate_tokens(payload)
    character_count = estimate_characters(payload)
    violations: list[str] = []
    if token_estimate > max_tokens:
        violations.append(f"{token_estimate} tokens > {max_tokens}")
    if max_characters is not None and character_count > max_characters:
        violations.append(f"{character_count} chars > {max_characters}")
    if violations:
        raise ValueError(
            f"stage input too large: {stage_name} {budget_label} exceeds budget "
            f"({' ; '.join(violations)})"
        )
    return token_estimate, character_count


def assert_no_raw_source_leakage(
    *,
    stage_name: str,
    payload: Any,
    raw_source_texts: list[str],
    min_probe_characters: int = 180,
) -> None:
    normalized_payload = _normalize_whitespace(serialize_for_budget(payload))
    for raw_text in raw_source_texts:
        normalized_source = _normalize_whitespace(raw_text)
        if len(normalized_source) < min_probe_characters:
            continue
        probe = normalized_source[:min_probe_characters]
        if probe and probe in normalized_payload:
            raise ValueError(f"raw source leakage into downstream stage: {stage_name}")
