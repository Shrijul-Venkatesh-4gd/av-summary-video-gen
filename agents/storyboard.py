from agno.agent import Agent

from agents.common import build_stage_model
from models.storyboard import Storyboard
from prompts.storyboard import STORYBOARD_AGENT_PROMPT
from utils.settings import OPENROUTER_MODEL_STORYBOARD, STAGE_OUTPUT_MAX_TOKENS_STORYBOARD


storyboarder = Agent(
    name="Instructional Storyboard Designer",
    model=build_stage_model(
        OPENROUTER_MODEL_STORYBOARD,
        STAGE_OUTPUT_MAX_TOKENS_STORYBOARD,
    ),
    output_schema=Storyboard,
    instructions=STORYBOARD_AGENT_PROMPT,
    markdown=False,
)
