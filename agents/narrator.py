from __future__ import annotations

import os
from typing import Any

from agno.agent import Agent
from agno.models.openai import OpenAIResponses

from knowledge.pdf_store import build_knowledge
from models.narrator_models import NarrationScript

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")


# ---------- Narration agent ----------

def build_narration_agent() -> Agent:
    knowledge = build_knowledge()

    return Agent(
        name="Narration Script Writer",
        model=OpenAIResponses(id=OPENAI_MODEL),
        knowledge=knowledge,
        search_knowledge=True,
        # Optional: also inject retrieved references directly into context
        add_knowledge_to_context=True,
        output_schema=NarrationScript,
        instructions=[
            "You create concise, spoken-video narration scripts grounded in the knowledge base.",
            "Always use the knowledge base before writing the final answer.",
            "Do not invent facts that are not supported by retrieved material.",
            "Compress repetitive slides into a smaller number of teaching sections.",
            "Write in a spoken, teacher-like tone. Do not sound like slide bullets.",
            "Prefer explanation over repetition.",
            "Each section should focus on one clear idea.",
            "Include useful visual notes for later animation in Manim.",
            "Include source_refs with filenames and page/section hints whenever possible.",
            "Do not include markdown fences or free-form prose outside the schema.",
        ],
        markdown=False,
    )


# ---------- Public function ----------

def _coerce_narration_script(content: Any) -> NarrationScript:
    if isinstance(content, NarrationScript):
        return content
    if isinstance(content, dict):
        return NarrationScript.model_validate(content)
    if isinstance(content, str):
        return NarrationScript.model_validate_json(content)
    raise TypeError(f"Unexpected narration response type: {type(content)!r}")


def generate_narration_script(
    topic: str,
    audience: str = "students",
    target_duration_min: int = 5,
) -> NarrationScript:
    agent = build_narration_agent()

    prompt = f"""
Create a narrated video script from the PDF knowledge base.

Topic focus: {topic}
Audience: {audience}
Target duration: about {target_duration_min} minutes

Requirements:
1. Search the knowledge base and ground the script in the retrieved PDF content.
2. Merge duplicate or repetitive slide content.
3. Produce a clean teaching flow, not a slide-by-slide reading.
4. Keep the narration suitable for voice synthesis.
5. For each section, include visual_notes that can later be turned into Manim scenes.
6. Fill source_refs with filenames, page numbers, or section clues from the retrieved material.
7. Keep the total duration close to the requested target.
"""

    response = agent.run(prompt)
    return _coerce_narration_script(response.content)


if __name__ == "__main__":
    script = generate_narration_script(
        topic="Introduction to computational problem solving in Python",
        audience="first-year engineering students",
        target_duration_min=4,
    )

    print(script.model_dump_json(indent=2))
