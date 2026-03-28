# av-summary-video-gen

This project turns grounded PDF knowledge into teaching-first Manim lesson videos.

The rendering layer now uses a reusable dark-theme explainer-video design system instead of generating ad hoc slide-like Manim scenes.

## Pipeline

The workflow now runs in five stages:

1. PDF ingestion and retrieval
2. Grounded-notes compression
3. Teaching-outline generation
4. Storyboard generation
5. Template-driven Manim plan and scene-module generation

The key shift is that the system no longer jumps straight from retrieved knowledge to narration-like scenes. It first creates a teaching outline, then a structured storyboard, and only then generates Manim code.

## Architecture

- `agents/grounded_notes.py`
  Compresses retrieved chunks into a bounded `GroundedNotes` artifact.
- `agents/narrator.py`
  Produces a grounded `TeachingOutline` from `grounded_notes.json`.
- `agents/storyboard.py`
  Converts the outline into a pedagogically structured `Storyboard` without raw retrieval text.
- `agents/builder.py`
  Builds a `ManimVideoPlan` deterministically from the storyboard using scene templates.
- `knowledge/retrieval.py`
  Performs one bounded vector-store retrieval call with dedupe and token/character budgets.
- `models/grounded_notes.py`
  Schema for the compact grounded-notes artifact passed into lesson planning.
- `models/observability.py`
  Schemas for retrieval stats, stage token estimates, and manifest metadata.
- `models/teaching_outline.py`
  Schema for teacher-oriented lesson sections.
- `models/storyboard.py`
  Schema for scene-level learning goals, visual focus, semantic color roles, layouts, animation plans, and asset requests.
- `models/builder.py`
  Schema for render-ready Manim scene plans.
- `visuals/theme.py`
  Shared dark-theme tokens: palette, typography scale, spacing, motion, stroke, and semantic color roles.
- `visuals/components.py`
  Reusable Manim UI primitives such as title blocks, concept nodes, callout boxes, process boxes, recap cards, and code panels.
- `visuals/scene_templates.py`
  Template metadata plus deterministic runtime renderers for concept maps, flows, quizzes, recaps, comparisons, and more.
- `visuals/assets.py`
  Optional primitive-built icons and symbols that stay generic and reusable.
- `utils/scene_templates.py`
  Compatibility re-export for the shared scene-template catalog.
- `utils/assets.py`
  Compatibility re-export for the shared primitive asset catalog.
- `utils/validation.py`
  Storyboard quality, semantic-visual, and pedagogical-diversity validation.

## Output Artifacts

Each successful workflow run saves inspectable artifacts such as:

- `retrieved_sources.json`
- `grounded_notes.json`
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
- Use a constrained semantic color system instead of scene-by-scene random colors.
- Let templates enforce polish so scenes feel like one coherent course-video system.
- Stay faithful to the ingested PDF material.
