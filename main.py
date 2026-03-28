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
from models.storyboard import Storyboard
from models.teaching_outline import TeachingOutline
from models.validation import StoryboardValidationReport
from utils.scene_templates import build_scene_template_brief
from utils.validation import validate_storyboard

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
    description="FastAPI service for PDF ingestion, teaching-outline generation, storyboard design, and Manim planning.",
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
) -> ArtifactResponse:
    manifest = ArtifactManifest(
        endpoint=endpoint,
        run_id=run_id,
        created_at=created_at,
        artifact_dir=str(artifact_dir.resolve()),
        request_path=request_path,
        artifacts=artifacts,
        notes=notes or [],
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


def _run_teaching_outline_agent(
    topic: str,
    audience: str,
    duration_min: int,
) -> TeachingOutline:
    from agents.narrator import teaching_outline_agent

    prompt = dedent(
        f"""
        Create a grounded teaching outline using the knowledge base.

        Topic focus:
        {topic}

        Audience:
        {audience}

        Target duration:
        about {duration_min} minutes

        Design this like a beginner-friendly lesson, not like PDF notes.
        """
    ).strip()
    response = teaching_outline_agent.run(prompt)
    return _coerce_agent_content(response.content, TeachingOutline)


def _run_storyboard_agent(teaching_outline: TeachingOutline) -> Storyboard:
    from agents.storyboard import storyboarder

    prompt = dedent(
        f"""
        Convert this teaching outline into a storyboard for an instructional video.

        Teaching outline JSON:
        {teaching_outline.model_dump_json(indent=2)}

        Make scene-to-scene variety intentional and pedagogically justified.
        """
    ).strip()
    response = storyboarder.run(prompt)
    return _coerce_agent_content(response.content, Storyboard)


def _run_builder_agent(
    storyboard: Storyboard,
    validation_report: StoryboardValidationReport,
) -> ManimVideoPlan:
    from agents.builder import builder

    scene_template_briefs = [
        build_scene_template_brief(scene) for scene in storyboard.scenes
    ]
    prompt = dedent(
        f"""
        Convert this storyboard into a Manim video plan.

        Storyboard JSON:
        {storyboard.model_dump_json(indent=2)}

        Validation report JSON:
        {validation_report.model_dump_json(indent=2)}

        Scene template briefs:
        {json.dumps(scene_template_briefs, indent=2)}

        Respect the storyboard scene order exactly.
        """
    ).strip()
    response = builder.run(prompt)
    return _coerce_agent_content(response.content, ManimVideoPlan)


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

    teaching_outline = _run_teaching_outline_agent(
        topic=request.topic,
        audience=request.audience,
        duration_min=request.duration_min,
    )
    storyboard = _run_storyboard_agent(teaching_outline)
    validation_report = validate_storyboard(storyboard)
    _raise_if_invalid_storyboard(validation_report)
    plan = _sanitize_plan(_run_builder_agent(storyboard, validation_report), storyboard)
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
            "teaching_outline": teaching_outline_path,
            "storyboard": storyboard_path,
            "storyboard_validation": validation_path,
            "manim_plan": plan_path,
            "generated_scene_module": module_path,
        },
        notes=notes,
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
        teaching_outline = _run_teaching_outline_agent(
            topic=request.topic,
            audience=request.audience,
            duration_min=request.duration_min,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise _bad_request(exc) from exc

    run_id, created_at, artifact_dir = _create_artifact_dir(
        endpoint="outline",
        label=request.topic,
    )
    request_path = _write_json_artifact(
        artifact_dir / "request.json",
        request.model_dump(mode="json"),
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
        artifacts={"teaching_outline": outline_path},
    )


@app.post("/narrate", response_model=ArtifactResponse)
def narrate_endpoint(request: NarrateRequest) -> ArtifactResponse:
    try:
        teaching_outline = _run_teaching_outline_agent(
            topic=request.topic,
            audience=request.audience,
            duration_min=request.duration_min,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise _bad_request(exc) from exc

    run_id, created_at, artifact_dir = _create_artifact_dir(
        endpoint="narrate",
        label=request.topic,
    )
    request_path = _write_json_artifact(
        artifact_dir / "request.json",
        request.model_dump(mode="json"),
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
        artifacts={"teaching_outline": outline_path},
        notes=["The /narrate endpoint is a compatibility alias for /outline."],
    )


@app.post("/storyboard", response_model=ArtifactResponse)
def storyboard_endpoint(request: StoryboardRequest) -> ArtifactResponse:
    try:
        storyboard = _run_storyboard_agent(request.teaching_outline)
        validation_report = validate_storyboard(storyboard)
        _raise_if_invalid_storyboard(validation_report)
    except ValueError as exc:
        raise _bad_request(exc) from exc

    notes = _validation_notes(validation_report)
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
    )


@app.post("/build", response_model=ArtifactResponse)
def build_endpoint(request: BuildRequest) -> ArtifactResponse:
    try:
        validation_report = validate_storyboard(request.storyboard)
        _raise_if_invalid_storyboard(validation_report)
        plan = _sanitize_plan(
            _run_builder_agent(request.storyboard, validation_report),
            request.storyboard,
        )
    except ValueError as exc:
        raise _bad_request(exc) from exc

    notes = _validation_notes(validation_report)
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
