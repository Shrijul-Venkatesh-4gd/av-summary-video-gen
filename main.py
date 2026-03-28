from __future__ import annotations

import argparse
from pathlib import Path

from agents.builder import GENERATED_MANIM_DIR, generate_manim_plan, save_manim_plan
from agents.narrator import generate_narration_script
from knowledge.pdf_store import PDF_DIR, ingest_pdfs
from models.narrator_models import NarrationScript


PROJECT_ROOT = Path(__file__).resolve().parent
GENERATED_DIR = PROJECT_ROOT / "generated"
DEFAULT_NARRATION_PATH = GENERATED_DIR / "narration_script.json"
DEFAULT_PLAN_PATH = GENERATED_DIR / "manim_plan.json"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_ingest(pdf_dir: str) -> None:
    ingest_pdfs(pdf_dir)


def run_narrate(topic: str, audience: str, duration_min: int, output: str) -> None:
    script = generate_narration_script(
        topic=topic,
        audience=audience,
        target_duration_min=duration_min,
    )
    output_path = Path(output)
    _write_text(output_path, script.model_dump_json(indent=2))
    print(f"Saved narration script to: {output_path}")


def run_build(narration_path: str, plan_output: str, out_dir: str) -> None:
    narration = NarrationScript.model_validate_json(
        Path(narration_path).read_text(encoding="utf-8")
    )
    plan = generate_manim_plan(narration)
    plan_path = Path(plan_output)
    _write_text(plan_path, plan.model_dump_json(indent=2))
    save_manim_plan(plan, out_dir=out_dir)
    print(f"Saved Manim plan JSON to: {plan_path}")


def run_pipeline(
    topic: str,
    audience: str,
    duration_min: int,
    narration_output: str,
    plan_output: str,
    out_dir: str,
) -> None:
    script = generate_narration_script(
        topic=topic,
        audience=audience,
        target_duration_min=duration_min,
    )
    narration_path = Path(narration_output)
    _write_text(narration_path, script.model_dump_json(indent=2))
    print(f"Saved narration script to: {narration_path}")

    plan = generate_manim_plan(script)
    plan_path = Path(plan_output)
    _write_text(plan_path, plan.model_dump_json(indent=2))
    save_manim_plan(plan, out_dir=out_dir)
    print(f"Saved Manim plan JSON to: {plan_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PDF-to-video generation pipeline using Agno."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest PDF files into the Agno knowledge store.",
    )
    ingest_parser.add_argument("--pdf-dir", default=PDF_DIR)

    narrate_parser = subparsers.add_parser(
        "narrate",
        help="Generate a grounded narration script from the knowledge store.",
    )
    narrate_parser.add_argument("--topic", required=True)
    narrate_parser.add_argument("--audience", default="students")
    narrate_parser.add_argument("--duration-min", type=int, default=5)
    narrate_parser.add_argument("--output", default=str(DEFAULT_NARRATION_PATH))

    build_parser_cmd = subparsers.add_parser(
        "build",
        help="Generate a Manim plan and module from a narration JSON file.",
    )
    build_parser_cmd.add_argument("--narration", default=str(DEFAULT_NARRATION_PATH))
    build_parser_cmd.add_argument("--plan-output", default=str(DEFAULT_PLAN_PATH))
    build_parser_cmd.add_argument("--out-dir", default=str(GENERATED_MANIM_DIR))

    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run narration and Manim planning in one command after PDFs are ingested.",
    )
    pipeline_parser.add_argument("--topic", required=True)
    pipeline_parser.add_argument("--audience", default="students")
    pipeline_parser.add_argument("--duration-min", type=int, default=5)
    pipeline_parser.add_argument("--narration-output", default=str(DEFAULT_NARRATION_PATH))
    pipeline_parser.add_argument("--plan-output", default=str(DEFAULT_PLAN_PATH))
    pipeline_parser.add_argument("--out-dir", default=str(GENERATED_MANIM_DIR))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest(args.pdf_dir)
    elif args.command == "narrate":
        run_narrate(args.topic, args.audience, args.duration_min, args.output)
    elif args.command == "build":
        run_build(args.narration, args.plan_output, args.out_dir)
    elif args.command == "pipeline":
        run_pipeline(
            args.topic,
            args.audience,
            args.duration_min,
            args.narration_output,
            args.plan_output,
            args.out_dir,
        )


if __name__ == "__main__":
    main()
