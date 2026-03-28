# av-summary-video-gen

This project turns grounded PDF knowledge into teaching-first Manim lesson videos.

## Pipeline

The workflow now runs in five stages:

1. PDF ingestion and retrieval
2. Teaching-outline generation
3. Storyboard generation
4. Manim plan and scene-module generation
5. Rendering from the generated Manim module

The key shift is that the system no longer jumps straight from retrieved knowledge to narration-like scenes. It first creates a teaching outline, then a structured storyboard, and only then generates Manim code.

## Architecture

- `agents/narrator.py`
  Produces a grounded `TeachingOutline` from the PDF-backed knowledge base.
- `agents/storyboard.py`
  Converts the outline into a pedagogically structured `Storyboard`.
- `agents/builder.py`
  Builds a `ManimVideoPlan` from storyboard scenes plus scene-template guidance.
- `models/teaching_outline.py`
  Schema for teacher-oriented lesson sections.
- `models/storyboard.py`
  Schema for scene-level learning goals, layouts, animation plans, and asset requests.
- `models/builder.py`
  Schema for render-ready Manim scene plans.
- `utils/scene_templates.py`
  Controlled scene-template guidance for major instructional scene types.
- `utils/assets.py`
  Lightweight reusable asset catalog backed by Manim primitives.
- `utils/validation.py`
  Storyboard quality and pedagogical-diversity validation.

## Output Artifacts

Each successful workflow run saves inspectable artifacts such as:

- `teaching_outline.json`
- `storyboard.json`
- `storyboard_validation.json`
- `manim_plan.json`
- `generated_scene_module.py`
- `manifest.json`

## Design Principles

- Teach one main idea at a time.
- Prefer examples before abstraction.
- Use progressive reveal instead of static text walls.
- Keep visuals varied, purposeful, and readable.
- Use motion to direct attention and reduce cognitive overload.
- Stay faithful to the ingested PDF material.
