from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from models.builder import ManimVideoPlan
from prompts.storyboard import BUILDER_AGENT_PROMPT
from utils.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


builder = Agent(
    name="Manim Code Generator",
    model=OpenRouter(
        id=OPENROUTER_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    ),
    output_schema=ManimVideoPlan,
    instructions=BUILDER_AGENT_PROMPT,
    markdown=False,
)
