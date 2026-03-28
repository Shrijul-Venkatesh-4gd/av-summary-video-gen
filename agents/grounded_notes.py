from agno.agent import Agent

from agents.common import build_stage_model
from models.grounded_notes import GroundedNotes
from prompts.grounded_notes import GROUNDED_NOTES_AGENT_PROMPT
from utils.settings import OPENROUTER_MODEL_GROUNDED_NOTES, STAGE_OUTPUT_MAX_TOKENS_GROUNDED_NOTES


grounded_notes_agent = Agent(
    name="Grounded Notes Compressor",
    model=build_stage_model(
        OPENROUTER_MODEL_GROUNDED_NOTES,
        STAGE_OUTPUT_MAX_TOKENS_GROUNDED_NOTES,
    ),
    output_schema=GroundedNotes,
    instructions=GROUNDED_NOTES_AGENT_PROMPT,
    markdown=False,
)
