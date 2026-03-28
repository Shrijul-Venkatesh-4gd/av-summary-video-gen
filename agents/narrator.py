from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from knowledge.pdf_store import build_knowledge
from models.teaching_outline import TeachingOutline
from prompts.teaching_outline import TEACHING_OUTLINE_AGENT_PROMPT
from utils.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


teaching_outline_agent = Agent(
    name="Teaching Outline Writer",
    model=OpenRouter(
        id=OPENROUTER_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    ),
    knowledge=build_knowledge(),
    search_knowledge=True,
    add_knowledge_to_context=True,
    output_schema=TeachingOutline,
    instructions=TEACHING_OUTLINE_AGENT_PROMPT,
    markdown=False,
)

# Backward-compatible alias for older imports.
narrator = teaching_outline_agent
