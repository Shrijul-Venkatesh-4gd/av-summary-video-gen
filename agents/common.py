from agno.models.openrouter import OpenRouter

from utils.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL


def build_stage_model(model_id: str, max_tokens: int) -> OpenRouter:
    return OpenRouter(
        id=model_id,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        max_tokens=max_tokens,
    )
