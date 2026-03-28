from __future__ import annotations

import ast
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from textwrap import dedent
from typing import Any, TypeVar

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from knowledge.pdf_store import get_pdf_dir, ingest_pdfs
from knowledge.retrieval import retrieve_budgeted_chunks
from models.api import (
    ArtifactManifest,
    ArtifactResponse,
    BuildRequest,
    IngestRequest,
    NarrateRequest,
    OutlineRequest,
    StoryboardRequest,
    WorkflowRequest,
)
from models.builder import ManimVideoPlan, SceneCode
from models.grounded_notes import GroundedNotes
from models.observability import (
    RetrievedSourceChunk,
    RetrievalStats,
    StageMetrics,
    WorkflowManifestMetadata,
)
from models.storyboard import Storyboard
from models.teaching_outline import TeachingOutline
from models.validation import StoryboardValidationReport
from prompts.grounded_notes import GROUNDED_NOTES_AGENT_PROMPT
from prompts.storyboard import BUILDER_AGENT_PROMPT, STORYBOARD_AGENT_PROMPT
from prompts.teaching_outline import TEACHING_OUTLINE_AGENT_PROMPT
from utils.budgeting import (
    assert_no_raw_source_leakage,
    ensure_within_budget,
    estimate_tokens,
)
from utils.validation import validate_storyboard
from utils.settings import (
    MAX_BUILDER_CHARACTERS,
    MAX_BUILDER_INPUT_TOKENS,
    MAX_GROUNDED_NOTES_CHARACTERS,
    MAX_GROUNDED_NOTES_TOKENS,
    MAX_OUTLINE_CHARACTERS,
    MAX_OUTLINE_INPUT_TOKENS,
    MAX_STORYBOARD_CHARACTERS,
    MAX_STORYBOARD_INPUT_TOKENS,
    OPENROUTER_MODEL_BUILDER,
    OPENROUTER_MODEL_GROUNDED_NOTES,
    OPENROUTER_MODEL_STORYBOARD,
    OPENROUTER_MODEL_TEACHING_OUTLINE,
    STAGE_OUTPUT_MAX_TOKENS_BUILDER,
    STAGE_OUTPUT_MAX_TOKENS_GROUNDED_NOTES,
    STAGE_OUTPUT_MAX_TOKENS_OUTLINE,
    STAGE_OUTPUT_MAX_TOKENS_STORYBOARD,
)

PROJECT_ROOT = Path(__file__).resolve().parent
GENERATED_ROOT_DIR = PROJECT_ROOT / "generated"
_MANIM_IMPORT_LINE_RE = re.compile(
    r"^\s*(?:from\s+manim\s+import\s+\*|import\s+manim(?:\s+as\s+\w+)?)\s*$"
)
_FORBIDDEN_SCENE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\bSVGMobject\s*\(\s*['\"][^'\"]+\.svg['\"]"),
        "references a local SVG asset. Use Manim primitives instead.",
    ),
    (
        re.compile(r"\bImageMobject\s*\(\s*['\"][^'\"]+\.(?:png|jpg|jpeg|gif|webp|bmp|svg)['\"]"),
        "references a local image asset. Use Manim primitives instead.",
    ),
    (
        re.compile(r"\bCode\s*\(\s*['\"]"),
        "uses Code(...) with a positional string, which Manim often treats as a file path. Use Code(code_string=..., language=...) or Text instead.",
    ),
)
ModelT = TypeVar("ModelT", bound=BaseModel)

app = FastAPI(
    title="AV Summary Video Generator",
    description=(
        "FastAPI service for PDF ingestion, budgeted retrieval, grounded-notes "
        "compression, teaching-outline generation, storyboard design, and Manim planning."
    ),
)


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _slugify(value: str, fallback: str = "run") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:80] or fallback


def _create_artifact_dir(
    endpoint: str,
    label: str,
    out_dir: str | None = None,
) -> tuple[str, str, Path]:
    base_dir = Path(out_dir or GENERATED_ROOT_DIR).expanduser().resolve()
    timestamp = datetime.now(UTC)
    run_id = f"{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}_{_slugify(label, endpoint)}"
    artifact_dir = base_dir / endpoint / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return run_id, timestamp.isoformat(), artifact_dir


def _write_json_artifact(path: Path, payload: Any) -> str:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path.resolve())


def _write_manifest(
    *,
    endpoint: str,
    run_id: str,
    created_at: str,
    artifact_dir: Path,
    request_path: str,
    artifacts: dict[str, str],
    notes: list[str] | None = None,
    metadata: WorkflowManifestMetadata | None = None,
) -> ArtifactResponse:
    manifest = ArtifactManifest(
        endpoint=endpoint,
        run_id=run_id,
        created_at=created_at,
        artifact_dir=str(artifact_dir.resolve()),
        request_path=request_path,
        artifacts=artifacts,
        notes=notes or [],
        metadata={} if metadata is None else metadata.model_dump(mode="json"),
    )
    manifest_path = artifact_dir / "manifest.json"
    _write_json_artifact(manifest_path, manifest.model_dump(mode="json"))
    return ArtifactResponse(
        endpoint=endpoint,
        run_id=run_id,
        artifact_dir=str(artifact_dir.resolve()),
        manifest_path=str(manifest_path.resolve()),
        artifacts=artifacts,
        notes=manifest.notes,
    )


def _coerce_agent_content(content: Any, model_cls: type[ModelT]) -> ModelT:
    if content is None:
        raise ValueError("Agent returned no content.")
    if isinstance(content, model_cls):
        return content
    if isinstance(content, str):
        return model_cls.model_validate_json(content)
    return model_cls.model_validate(content)


def _normalize_scene_code(scene_code: str) -> str:
    cleaned_lines = [
        line
        for line in scene_code.splitlines()
        if not _MANIM_IMPORT_LINE_RE.match(line.strip())
    ]

    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    return "\n".join(cleaned_lines)


def _sanitize_scene(scene: SceneCode) -> SceneCode:
    normalized_code = _normalize_scene_code(scene.code)

    expected_class = re.compile(
        rf"class\s+{re.escape(scene.class_name)}\s*\(\s*Scene\s*\)\s*:"
    )
    if not expected_class.search(normalized_code):
        raise ValueError(
            f"Scene {scene.scene_id} does not define the expected class "
            f"{scene.class_name}."
        )

    for pattern, reason in _FORBIDDEN_SCENE_PATTERNS:
        if pattern.search(normalized_code):
            raise ValueError(f"Scene {scene.scene_id} contains code that {reason}")

    try:
        ast.parse(normalized_code)
    except SyntaxError as exc:
        raise ValueError(
            f"Scene {scene.scene_id} contains invalid Python: {exc.msg} "
            f"(line {exc.lineno})"
        ) from exc

    return scene.model_copy(update={"code": normalized_code})


def _sanitize_plan(plan: ManimVideoPlan, storyboard: Storyboard) -> ManimVideoPlan:
    expected_scene_ids = [scene.scene_id for scene in storyboard.scenes]
    actual_scene_ids = [scene.storyboard_scene_id for scene in plan.scenes]

    if set(actual_scene_ids) != set(expected_scene_ids):
        missing = sorted(set(expected_scene_ids) - set(actual_scene_ids))
        extra = sorted(set(actual_scene_ids) - set(expected_scene_ids))
        fragments = []
        if missing:
            fragments.append(f"missing storyboard scenes: {', '.join(missing)}")
        if extra:
            fragments.append(f"unexpected storyboard scenes: {', '.join(extra)}")
        raise ValueError("Builder output does not align with storyboard: " + "; ".join(fragments))
    if actual_scene_ids != expected_scene_ids:
        raise ValueError("Builder output scene order does not match the storyboard order.")

    sanitized_scenes = [_sanitize_scene(scene) for scene in plan.scenes]
    return plan.model_copy(update={"scenes": sanitized_scenes})


def _save_manim_plan(
    plan: ManimVideoPlan,
    out_dir: str | Path | None = None,
    *,
    filename: str = "generated_scene_module.py",
) -> str:
    output_dir = Path(out_dir or GENERATED_ROOT_DIR / "manim").expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    module_path = output_dir / filename
    module_lines = ["from manim import *", ""]
    if plan.shared_notes:
        module_lines.extend(f"# {note}" for note in plan.shared_notes)
        module_lines.append("")
    for scene in plan.scenes:
        module_lines.append(scene.code.rstrip())
        module_lines.append("")

    module_path.write_text("\n".join(module_lines).rstrip() + "\n", encoding="utf-8")
    return str(module_path.resolve())


def _validation_notes(report: StoryboardValidationReport) -> list[str]:
    notes: list[str] = []
    if report.warning_count:
        notes.append(
            f"Storyboard validation emitted {report.warning_count} warning(s). See storyboard_validation.json."
        )
    return notes


def _raise_if_invalid_storyboard(report: StoryboardValidationReport) -> None:
    if report.valid:
        return

    issue_lines = []
    for issue in report.issues:
        if issue.severity != "error":
            continue
        prefix = f"{issue.scene_id}: " if issue.scene_id else ""
        issue_lines.append(f"{prefix}{issue.message}")
    raise ValueError(
        "Storyboard validation failed with "
        f"{report.error_count} error(s): " + " | ".join(issue_lines[:5])
    )


def _log_retrieval_stats(stats: RetrievalStats) -> None:
    print(
        "[retrieval] "
        f"calls={stats.retrieval_calls}/{stats.max_retrieval_calls} "
        f"candidates={stats.candidate_chunks} selected={stats.selected_chunks} "
        f"tokens~{stats.source_tokens_estimate} chars={stats.source_characters}"
    )


def _log_stage_metrics(metric: StageMetrics) -> None:
    print(
        f"[{metric.stage_name}] "
        f"model={metric.model} "
        f"input_tokens~{metric.input_tokens_estimate}/{metric.input_tokens_limit} "
        f"output_tokens~{metric.output_tokens_estimate}/{metric.output_tokens_limit} "
        f"bytes={metric.serialized_artifact_bytes} "
        f"compression={metric.compression_applied} "
        f"truncation={metric.truncation_applied}"
    )


def _make_stage_metric(
    *,
    stage_name: str,
    model: str,
    input_payload: Any,
    input_limit: int,
    output_payload: Any,
    output_limit: int,
    compression_applied: bool = False,
    truncation_applied: bool = False,
    warnings: list[str] | None = None,
) -> StageMetrics:
    serialized_output = (
        output_payload.model_dump_json(indent=2, exclude_none=True)
        if isinstance(output_payload, BaseModel)
        else json.dumps(output_payload, indent=2, ensure_ascii=False, default=str)
    )
    metric = StageMetrics(
        stage_name=stage_name,
        model=model,
        input_tokens_estimate=estimate_tokens(input_payload),
        input_tokens_limit=input_limit,
        output_tokens_estimate=estimate_tokens(serialized_output),
        output_tokens_limit=output_limit,
        serialized_artifact_bytes=len(serialized_output.encode("utf-8")),
        compression_applied=compression_applied,
        truncation_applied=truncation_applied,
        warnings=warnings or [],
    )
    _log_stage_metrics(metric)
    return metric


def _retrieval_query(topic: str, audience: str, duration_min: int) -> str:
    return dedent(
        f"""
        Topic: {topic}
        Audience: {audience}
        Requested duration: about {duration_min} minutes

        Retrieve only the most relevant chunks needed to explain this topic accurately to this audience.
        """
    ).strip()


def _run_grounded_notes_stage(
    *,
    topic: str,
    audience: str,
    duration_min: int,
) -> tuple[GroundedNotes, list[RetrievedSourceChunk], RetrievalStats, StageMetrics]:
    from agents.grounded_notes import grounded_notes_agent

    retrieval_query = _retrieval_query(topic, audience, duration_min)
    retrieved_chunks, retrieval_stats = retrieve_budgeted_chunks(retrieval_query)
    _log_retrieval_stats(retrieval_stats)

    chunk_payload = [
        {
            "chunk_id": chunk.chunk_id,
            "document_name": chunk.document_name,
            "locator": chunk.locator,
            "similarity_score": chunk.similarity_score,
            "content": chunk.content,
        }
        for chunk in retrieved_chunks
    ]
    prompt = dedent(
        f"""
        Create compact grounded notes for this lesson request.

        Request:
        {json.dumps(
            {
                "topic": topic,
                "audience": audience,
                "duration_min": duration_min,
            },
            indent=2,
        )}

        Retrieved evidence JSON:
        {json.dumps(chunk_payload, indent=2)}

        Keep the artifact compact because later stages only receive these grounded notes.
        """
    ).strip()
    ensure_within_budget(
        stage_name="grounded_notes",
        payload=f"{GROUNDED_NOTES_AGENT_PROMPT}\n\n{prompt}",
        max_tokens=retrieval_stats.source_tokens_estimate + MAX_GROUNDED_NOTES_TOKENS,
        max_characters=retrieval_stats.source_characters + MAX_GROUNDED_NOTES_CHARACTERS,
        budget_label="retrieval compression input",
    )
    response = grounded_notes_agent.run(prompt)
    grounded_notes = _coerce_agent_content(response.content, GroundedNotes)
    retrieval_stats = retrieval_stats.model_copy(update={"compression_applied": True})
    ensure_within_budget(
        stage_name="grounded_notes",
        payload=grounded_notes,
        max_tokens=MAX_GROUNDED_NOTES_TOKENS,
        max_characters=MAX_GROUNDED_NOTES_CHARACTERS,
        budget_label="artifact",
    )
    stage_metric = _make_stage_metric(
        stage_name="grounded_notes",
        model=OPENROUTER_MODEL_GROUNDED_NOTES,
        input_payload=f"{GROUNDED_NOTES_AGENT_PROMPT}\n\n{prompt}",
        input_limit=retrieval_stats.source_tokens_estimate + MAX_GROUNDED_NOTES_TOKENS,
        output_payload=grounded_notes,
        output_limit=STAGE_OUTPUT_MAX_TOKENS_GROUNDED_NOTES,
        compression_applied=True,
        warnings=list(retrieval_stats.warnings),
    )
    return grounded_notes, retrieved_chunks, retrieval_stats, stage_metric


def _run_teaching_outline_agent(
    topic: str,
    audience: str,
    duration_min: int,
    grounded_notes: GroundedNotes,
    retrieved_chunks: list[RetrievedSourceChunk],
) -> tuple[TeachingOutline, StageMetrics]:
    from agents.narrator import teaching_outline_agent

    prompt = dedent(
        f"""
        Create a teaching outline from these grounded notes.

        Request:
        {json.dumps(
            {
                "topic": topic,
                "audience": audience,
                "duration_min": duration_min,
            },
            indent=2,
        )}

        Grounded notes JSON:
        {grounded_notes.model_dump_json(indent=2)}

        Keep the lesson tightly scoped and beginner-friendly.
        """
    ).strip()
    assert_no_raw_source_leakage(
        stage_name="teaching_outline",
        payload=prompt,
        raw_source_texts=[chunk.content for chunk in retrieved_chunks],
    )
    ensure_within_budget(
        stage_name="teaching_outline",
        payload=f"{TEACHING_OUTLINE_AGENT_PROMPT}\n\n{prompt}",
        max_tokens=MAX_OUTLINE_INPUT_TOKENS,
        max_characters=MAX_OUTLINE_CHARACTERS,
    )
    response = teaching_outline_agent.run(prompt)
    teaching_outline = _coerce_agent_content(response.content, TeachingOutline)
    stage_metric = _make_stage_metric(
        stage_name="teaching_outline",
        model=OPENROUTER_MODEL_TEACHING_OUTLINE,
        input_payload=f"{TEACHING_OUTLINE_AGENT_PROMPT}\n\n{prompt}",
        input_limit=MAX_OUTLINE_INPUT_TOKENS,
        output_payload=teaching_outline,
        output_limit=STAGE_OUTPUT_MAX_TOKENS_OUTLINE,
    )
    return teaching_outline, stage_metric


def _run_storyboard_agent(
    teaching_outline: TeachingOutline,
    retrieved_chunks: list[RetrievedSourceChunk] | None = None,
) -> tuple[Storyboard, StageMetrics]:
    from agents.storyboard import storyboarder

    prompt = dedent(
        f"""
        Convert this teaching outline into a storyboard for an instructional video.

        Teaching outline JSON:
        {teaching_outline.model_dump_json(indent=2)}

        Keep scene count and on-screen text tightly bounded.
        """
    ).strip()
    if retrieved_chunks is not None:
        assert_no_raw_source_leakage(
            stage_name="storyboard",
            payload=prompt,
            raw_source_texts=[chunk.content for chunk in retrieved_chunks],
        )
    ensure_within_budget(
        stage_name="storyboard",
        payload=f"{STORYBOARD_AGENT_PROMPT}\n\n{prompt}",
        max_tokens=MAX_STORYBOARD_INPUT_TOKENS,
        max_characters=MAX_STORYBOARD_CHARACTERS,
    )
    response = storyboarder.run(prompt)
    storyboard = _coerce_agent_content(response.content, Storyboard)
    stage_metric = _make_stage_metric(
        stage_name="storyboard",
        model=OPENROUTER_MODEL_STORYBOARD,
        input_payload=f"{STORYBOARD_AGENT_PROMPT}\n\n{prompt}",
        input_limit=MAX_STORYBOARD_INPUT_TOKENS,
        output_payload=storyboard,
        output_limit=STAGE_OUTPUT_MAX_TOKENS_STORYBOARD,
    )
    return storyboard, stage_metric


def _run_builder_agent(
    storyboard: Storyboard,
    retrieved_chunks: list[RetrievedSourceChunk] | None = None,
) -> tuple[ManimVideoPlan, StageMetrics]:
    from agents.builder import builder

    prompt = dedent(
        f"""
        Convert this storyboard into a Manim video plan.

        Storyboard JSON:
        {storyboard.model_dump_json(indent=2)}

        Respect the storyboard scene order exactly.
        """
    ).strip()
    if retrieved_chunks is not None:
        assert_no_raw_source_leakage(
            stage_name="builder",
            payload=prompt,
            raw_source_texts=[chunk.content for chunk in retrieved_chunks],
        )
    ensure_within_budget(
        stage_name="builder",
        payload=f"{BUILDER_AGENT_PROMPT}\n\n{prompt}",
        max_tokens=MAX_BUILDER_INPUT_TOKENS,
        max_characters=MAX_BUILDER_CHARACTERS,
    )
    response = builder.run(prompt)
    plan = _coerce_agent_content(response.content, ManimVideoPlan)
    stage_metric = _make_stage_metric(
        stage_name="builder",
        model=OPENROUTER_MODEL_BUILDER,
        input_payload=f"{BUILDER_AGENT_PROMPT}\n\n{prompt}",
        input_limit=MAX_BUILDER_INPUT_TOKENS,
        output_payload=plan,
        output_limit=STAGE_OUTPUT_MAX_TOKENS_BUILDER,
    )
    return plan, stage_metric


def _run_outline_stack(
    *,
    topic: str,
    audience: str,
    duration_min: int,
) -> tuple[
    GroundedNotes,
    list[RetrievedSourceChunk],
    RetrievalStats,
    TeachingOutline,
    list[StageMetrics],
]:
    grounded_notes, retrieved_chunks, retrieval_stats, grounded_notes_metric = _run_grounded_notes_stage(
        topic=topic,
        audience=audience,
        duration_min=duration_min,
    )
    teaching_outline, outline_metric = _run_teaching_outline_agent(
        topic=topic,
        audience=audience,
        duration_min=duration_min,
        grounded_notes=grounded_notes,
        retrieved_chunks=retrieved_chunks,
    )
    return (
        grounded_notes,
        retrieved_chunks,
        retrieval_stats,
        teaching_outline,
        [grounded_notes_metric, outline_metric],
    )


def _run_workflow(request: WorkflowRequest) -> ArtifactResponse:
    ingestion_summary = {
        "pdf_dir": str(Path(request.pdf_dir or get_pdf_dir()).expanduser().resolve()),
        "processed_files": [],
        "ingested_files": [],
        "skipped_files": [],
        "registry_path": "",
        "force_reingest": request.force_reingest,
    }
    if request.run_ingestion:
        ingestion_result = ingest_pdfs(
            request.pdf_dir,
            force_reingest=request.force_reingest,
        )
        ingestion_summary = {
            "pdf_dir": str(ingestion_result.pdf_dir),
            "processed_files": [str(path) for path in ingestion_result.processed_files],
            "ingested_files": [str(path) for path in ingestion_result.ingested_files],
            "skipped_files": [str(path) for path in ingestion_result.skipped_files],
            "registry_path": str(ingestion_result.registry_path),
            "force_reingest": request.force_reingest,
        }

    (
        grounded_notes,
        retrieved_chunks,
        retrieval_stats,
        teaching_outline,
        stage_metrics,
    ) = _run_outline_stack(
        topic=request.topic,
        audience=request.audience,
        duration_min=request.duration_min,
    )
    storyboard, storyboard_metric = _run_storyboard_agent(teaching_outline, retrieved_chunks)
    validation_report = validate_storyboard(storyboard)
    _raise_if_invalid_storyboard(validation_report)
    plan, builder_metric = _run_builder_agent(storyboard, retrieved_chunks)
    plan = _sanitize_plan(plan, storyboard)

    metadata = WorkflowManifestMetadata(
        retrieval_stats=retrieval_stats,
        stage_metrics=[*stage_metrics, storyboard_metric, builder_metric],
        compression_decisions=["Compressed retrieved chunks into grounded_notes.json before lesson generation."],
        truncation_decisions=[],
        warnings=[*retrieval_stats.warnings],
    )

    notes = _validation_notes(validation_report)
    run_id, created_at, artifact_dir = _create_artifact_dir(
        endpoint="workflow",
        label=request.topic,
        out_dir=request.out_dir,
    )

    request_path = _write_json_artifact(
        artifact_dir / "request.json",
        request.model_dump(mode="json"),
    )
    ingestion_path = _write_json_artifact(
        artifact_dir / "ingestion.json",
        ingestion_summary,
    )
    retrieval_path = _write_json_artifact(
        artifact_dir / "retrieved_sources.json",
        [chunk.model_dump(mode="json") for chunk in retrieved_chunks],
    )
    grounded_notes_path = _write_json_artifact(
        artifact_dir / "grounded_notes.json",
        grounded_notes.model_dump(mode="json"),
    )
    teaching_outline_path = _write_json_artifact(
        artifact_dir / "teaching_outline.json",
        teaching_outline.model_dump(mode="json"),
    )
    storyboard_path = _write_json_artifact(
        artifact_dir / "storyboard.json",
        storyboard.model_dump(mode="json"),
    )
    validation_path = _write_json_artifact(
        artifact_dir / "storyboard_validation.json",
        validation_report.model_dump(mode="json"),
    )
    plan_path = _write_json_artifact(
        artifact_dir / "manim_plan.json",
        plan.model_dump(mode="json"),
    )
    module_path = _save_manim_plan(plan, artifact_dir)

    return _write_manifest(
        endpoint="workflow",
        run_id=run_id,
        created_at=created_at,
        artifact_dir=artifact_dir,
        request_path=request_path,
        artifacts={
            "ingestion": ingestion_path,
            "retrieved_sources": retrieval_path,
            "grounded_notes": grounded_notes_path,
            "teaching_outline": teaching_outline_path,
            "storyboard": storyboard_path,
            "storyboard_validation": validation_path,
            "manim_plan": plan_path,
            "generated_scene_module": module_path,
        },
        notes=notes,
        metadata=metadata,
    )


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest", response_model=ArtifactResponse)
def ingest_endpoint(request: IngestRequest) -> ArtifactResponse:
    try:
        ingestion_result = ingest_pdfs(
            request.pdf_dir,
            force_reingest=request.force_reingest,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise _bad_request(exc) from exc

    run_id, created_at, artifact_dir = _create_artifact_dir(
        endpoint="ingest",
        label=ingestion_result.pdf_dir.name,
    )
    request_path = _write_json_artifact(
        artifact_dir / "request.json",
        request.model_dump(mode="json"),
    )
    ingest_response_path = _write_json_artifact(
        artifact_dir / "ingest_response.json",
        {
            "pdf_dir": str(ingestion_result.pdf_dir),
            "processed_files": [str(path) for path in ingestion_result.processed_files],
            "ingested_files": [str(path) for path in ingestion_result.ingested_files],
            "skipped_files": [str(path) for path in ingestion_result.skipped_files],
            "registry_path": str(ingestion_result.registry_path),
            "force_reingest": request.force_reingest,
        },
    )

    return _write_manifest(
        endpoint="ingest",
        run_id=run_id,
        created_at=created_at,
        artifact_dir=artifact_dir,
        request_path=request_path,
        artifacts={"ingest_response": ingest_response_path},
    )


@app.post("/outline", response_model=ArtifactResponse)
def outline_endpoint(request: OutlineRequest) -> ArtifactResponse:
    try:
        (
            grounded_notes,
            retrieved_chunks,
            retrieval_stats,
            teaching_outline,
            stage_metrics,
        ) = _run_outline_stack(
            topic=request.topic,
            audience=request.audience,
            duration_min=request.duration_min,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise _bad_request(exc) from exc

    metadata = WorkflowManifestMetadata(
        retrieval_stats=retrieval_stats,
        stage_metrics=stage_metrics,
        compression_decisions=["Compressed retrieved chunks into grounded_notes.json before outline generation."],
        warnings=[*retrieval_stats.warnings],
    )
    run_id, created_at, artifact_dir = _create_artifact_dir(
        endpoint="outline",
        label=request.topic,
    )
    request_path = _write_json_artifact(
        artifact_dir / "request.json",
        request.model_dump(mode="json"),
    )
    retrieval_path = _write_json_artifact(
        artifact_dir / "retrieved_sources.json",
        [chunk.model_dump(mode="json") for chunk in retrieved_chunks],
    )
    grounded_notes_path = _write_json_artifact(
        artifact_dir / "grounded_notes.json",
        grounded_notes.model_dump(mode="json"),
    )
    outline_path = _write_json_artifact(
        artifact_dir / "teaching_outline.json",
        teaching_outline.model_dump(mode="json"),
    )

    return _write_manifest(
        endpoint="outline",
        run_id=run_id,
        created_at=created_at,
        artifact_dir=artifact_dir,
        request_path=request_path,
        artifacts={
            "retrieved_sources": retrieval_path,
            "grounded_notes": grounded_notes_path,
            "teaching_outline": outline_path,
        },
        metadata=metadata,
    )


@app.post("/narrate", response_model=ArtifactResponse)
def narrate_endpoint(request: NarrateRequest) -> ArtifactResponse:
    try:
        (
            grounded_notes,
            retrieved_chunks,
            retrieval_stats,
            teaching_outline,
            stage_metrics,
        ) = _run_outline_stack(
            topic=request.topic,
            audience=request.audience,
            duration_min=request.duration_min,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise _bad_request(exc) from exc

    metadata = WorkflowManifestMetadata(
        retrieval_stats=retrieval_stats,
        stage_metrics=stage_metrics,
        compression_decisions=["Compressed retrieved chunks into grounded_notes.json before outline generation."],
        warnings=[*retrieval_stats.warnings],
    )
    run_id, created_at, artifact_dir = _create_artifact_dir(
        endpoint="narrate",
        label=request.topic,
    )
    request_path = _write_json_artifact(
        artifact_dir / "request.json",
        request.model_dump(mode="json"),
    )
    retrieval_path = _write_json_artifact(
        artifact_dir / "retrieved_sources.json",
        [chunk.model_dump(mode="json") for chunk in retrieved_chunks],
    )
    grounded_notes_path = _write_json_artifact(
        artifact_dir / "grounded_notes.json",
        grounded_notes.model_dump(mode="json"),
    )
    outline_path = _write_json_artifact(
        artifact_dir / "teaching_outline.json",
        teaching_outline.model_dump(mode="json"),
    )

    return _write_manifest(
        endpoint="narrate",
        run_id=run_id,
        created_at=created_at,
        artifact_dir=artifact_dir,
        request_path=request_path,
        artifacts={
            "retrieved_sources": retrieval_path,
            "grounded_notes": grounded_notes_path,
            "teaching_outline": outline_path,
        },
        notes=["The /narrate endpoint is a compatibility alias for /outline."],
        metadata=metadata,
    )


@app.post("/storyboard", response_model=ArtifactResponse)
def storyboard_endpoint(request: StoryboardRequest) -> ArtifactResponse:
    try:
        storyboard, storyboard_metric = _run_storyboard_agent(request.teaching_outline)
        validation_report = validate_storyboard(storyboard)
        _raise_if_invalid_storyboard(validation_report)
    except ValueError as exc:
        raise _bad_request(exc) from exc

    notes = _validation_notes(validation_report)
    metadata = WorkflowManifestMetadata(stage_metrics=[storyboard_metric], warnings=notes)
    run_id, created_at, artifact_dir = _create_artifact_dir(
        endpoint="storyboard",
        label=request.teaching_outline.video_title,
        out_dir=request.out_dir,
    )
    request_path = _write_json_artifact(
        artifact_dir / "request.json",
        request.model_dump(mode="json"),
    )
    outline_path = _write_json_artifact(
        artifact_dir / "teaching_outline.json",
        request.teaching_outline.model_dump(mode="json"),
    )
    storyboard_path = _write_json_artifact(
        artifact_dir / "storyboard.json",
        storyboard.model_dump(mode="json"),
    )
    validation_path = _write_json_artifact(
        artifact_dir / "storyboard_validation.json",
        validation_report.model_dump(mode="json"),
    )

    return _write_manifest(
        endpoint="storyboard",
        run_id=run_id,
        created_at=created_at,
        artifact_dir=artifact_dir,
        request_path=request_path,
        artifacts={
            "teaching_outline": outline_path,
            "storyboard": storyboard_path,
            "storyboard_validation": validation_path,
        },
        notes=notes,
        metadata=metadata,
    )


@app.post("/build", response_model=ArtifactResponse)
def build_endpoint(request: BuildRequest) -> ArtifactResponse:
    try:
        validation_report = validate_storyboard(request.storyboard)
        _raise_if_invalid_storyboard(validation_report)
        plan, builder_metric = _run_builder_agent(request.storyboard)
        plan = _sanitize_plan(plan, request.storyboard)
    except ValueError as exc:
        raise _bad_request(exc) from exc

    notes = _validation_notes(validation_report)
    metadata = WorkflowManifestMetadata(stage_metrics=[builder_metric], warnings=notes)
    run_id, created_at, artifact_dir = _create_artifact_dir(
        endpoint="build",
        label=request.storyboard.video_title,
        out_dir=request.out_dir,
    )
    request_path = _write_json_artifact(
        artifact_dir / "request.json",
        request.model_dump(mode="json"),
    )
    storyboard_path = _write_json_artifact(
        artifact_dir / "storyboard.json",
        request.storyboard.model_dump(mode="json"),
    )
    validation_path = _write_json_artifact(
        artifact_dir / "storyboard_validation.json",
        validation_report.model_dump(mode="json"),
    )
    plan_path = _write_json_artifact(
        artifact_dir / "manim_plan.json",
        plan.model_dump(mode="json"),
    )
    module_path = _save_manim_plan(plan, artifact_dir)

    return _write_manifest(
        endpoint="build",
        run_id=run_id,
        created_at=created_at,
        artifact_dir=artifact_dir,
        request_path=request_path,
        artifacts={
            "storyboard": storyboard_path,
            "storyboard_validation": validation_path,
            "manim_plan": plan_path,
            "generated_scene_module": module_path,
        },
        notes=notes,
        metadata=metadata,
    )


@app.post("/workflow", response_model=ArtifactResponse)
def workflow_endpoint(request: WorkflowRequest) -> ArtifactResponse:
    try:
        return _run_workflow(request)
    except (FileNotFoundError, ValueError) as exc:
        raise _bad_request(exc) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
