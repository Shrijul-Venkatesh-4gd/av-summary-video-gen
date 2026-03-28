from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from models.storyboard import Storyboard
from prompts.storyboard import STORYBOARD_AGENT_PROMPT
from utils.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


storyboarder = Agent(
    name="Instructional Storyboard Designer",
    model=OpenRouter(
        id=OPENROUTER_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    ),
    output_schema=Storyboard,
    instructions=STORYBOARD_AGENT_PROMPT,
    markdown=False,
)
