from __future__ import annotations

from difflib import SequenceMatcher
import re

from agno.knowledge.document.base import Document

from knowledge.pdf_store import build_knowledge
from models.observability import RetrievedSourceChunk, RetrievalStats
from utils.budgeting import estimate_tokens
from utils.settings import (
    MAX_RETRIEVAL_CALLS_PER_WORKFLOW,
    MAX_RETRIEVED_CHUNKS,
    MAX_SOURCE_CHARACTERS,
    MAX_SOURCE_TOKENS,
    RETRIEVAL_DEDUPLICATION_THRESHOLD,
    RETRIEVAL_SEARCH_CANDIDATES,
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _is_high_overlap(candidate: str, accepted: list[str]) -> bool:
    normalized_candidate = _normalize_text(candidate)
    if not normalized_candidate:
        return True
    for existing in accepted:
        ratio = SequenceMatcher(None, normalized_candidate, _normalize_text(existing)).ratio()
        if ratio >= RETRIEVAL_DEDUPLICATION_THRESHOLD:
            return True
    return False


def _locator_for_document(document: Document) -> str:
    meta_data = document.meta_data or {}
    parts: list[str] = []
    if meta_data.get("page") is not None:
        parts.append(f"page {meta_data['page']}")
    if meta_data.get("chunk") is not None:
        parts.append(f"chunk {meta_data['chunk']}")
    if not parts:
        return "document-level chunk"
    return ", ".join(parts)


def _score_for_document(document: Document) -> float:
    meta_data = document.meta_data or {}
    similarity_score = meta_data.get("similarity_score")
    return float(similarity_score) if similarity_score is not None else 0.0


def retrieve_budgeted_chunks(
    query: str,
    *,
    retrieval_calls_so_far: int = 0,
) -> tuple[list[RetrievedSourceChunk], RetrievalStats]:
    if retrieval_calls_so_far >= MAX_RETRIEVAL_CALLS_PER_WORKFLOW:
        raise ValueError("retrieval budget exceeded: max retrieval calls per workflow reached")

    knowledge = build_knowledge()
    raw_documents = knowledge.search(query=query, max_results=RETRIEVAL_SEARCH_CANDIDATES)
    ranked_documents = sorted(raw_documents, key=_score_for_document, reverse=True)

    selected_chunks: list[RetrievedSourceChunk] = []
    accepted_texts: list[str] = []
    token_total = 0
    char_total = 0
    warnings: list[str] = []
    deduplicated_count = 0

    for document in ranked_documents:
        content = (document.content or "").strip()
        if not content:
            continue
        if _is_high_overlap(content, accepted_texts):
            deduplicated_count += 1
            continue

        token_estimate = estimate_tokens(content)
        character_count = len(content)
        would_exceed_chunk_budget = len(selected_chunks) >= MAX_RETRIEVED_CHUNKS
        would_exceed_token_budget = token_total + token_estimate > MAX_SOURCE_TOKENS
        would_exceed_character_budget = char_total + character_count > MAX_SOURCE_CHARACTERS
        if would_exceed_chunk_budget or would_exceed_token_budget or would_exceed_character_budget:
            warnings.append("retrieval budget exceeded")
            break

        selected_chunks.append(
            RetrievedSourceChunk(
                chunk_id=document.id or f"{document.name}_{len(selected_chunks) + 1}",
                document_name=document.name or "unknown_document",
                locator=_locator_for_document(document),
                similarity_score=_score_for_document(document),
                token_estimate=token_estimate,
                character_count=character_count,
                content=content,
            )
        )
        accepted_texts.append(content)
        token_total += token_estimate
        char_total += character_count

    if not selected_chunks:
        raise ValueError("No retrieved evidence fit within the configured retrieval budget.")

    return selected_chunks, RetrievalStats(
        query=query,
        retrieval_calls=retrieval_calls_so_far + 1,
        max_retrieval_calls=MAX_RETRIEVAL_CALLS_PER_WORKFLOW,
        candidate_chunks=len(raw_documents),
        deduplicated_chunks=deduplicated_count,
        selected_chunks=len(selected_chunks),
        source_tokens_estimate=token_total,
        source_characters=char_total,
        max_retrieved_chunks=MAX_RETRIEVED_CHUNKS,
        max_source_tokens=MAX_SOURCE_TOKENS,
        max_source_characters=MAX_SOURCE_CHARACTERS,
        search_candidates=RETRIEVAL_SEARCH_CANDIDATES,
        compression_applied=False,
        truncation_applied=False,
        warnings=warnings,
    )
