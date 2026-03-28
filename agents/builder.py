from agno.agent import Agent

from agents.common import build_stage_model
from models.builder import ManimVideoPlan
from prompts.storyboard import BUILDER_AGENT_PROMPT
from utils.settings import OPENROUTER_MODEL_BUILDER, STAGE_OUTPUT_MAX_TOKENS_BUILDER


builder = Agent(
    name="Manim Code Generator",
    model=build_stage_model(
        OPENROUTER_MODEL_BUILDER,
        STAGE_OUTPUT_MAX_TOKENS_BUILDER,
    ),
    output_schema=ManimVideoPlan,
    instructions=BUILDER_AGENT_PROMPT,
    markdown=False,
)
