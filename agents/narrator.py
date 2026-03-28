from agno.agent import Agent

from agents.common import build_stage_model
from models.teaching_outline import TeachingOutline
from prompts.teaching_outline import TEACHING_OUTLINE_AGENT_PROMPT
from utils.settings import (
    OPENROUTER_MODEL_TEACHING_OUTLINE,
    STAGE_OUTPUT_MAX_TOKENS_OUTLINE,
)


teaching_outline_agent = Agent(
    name="Teaching Outline Writer",
    model=build_stage_model(
        OPENROUTER_MODEL_TEACHING_OUTLINE,
        STAGE_OUTPUT_MAX_TOKENS_OUTLINE,
    ),
    output_schema=TeachingOutline,
    instructions=TEACHING_OUTLINE_AGENT_PROMPT,
    markdown=False,
)

# Backward-compatible alias for older imports.
narrator = teaching_outline_agent
