"""ADK agent wired to z.AI via LiteLLM."""

import mimetypes

import litellm
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

import config
from tools import ALL_TOOLS


class AgentError(Exception):
    """Raised when the agent cannot complete a run."""


class InsufficientBalanceError(AgentError):
    """Raised when the API returns a billing/quota error."""


class AuthenticationError(AgentError):
    """Raised when the API key is missing or rejected."""

SYSTEM_PROMPT = """\
You are an expert image editing agent. You have access to a set of ImageMagick-powered tools.

Your workflow for every request:
1. Call get_image_info() to understand the image dimensions, format, and colorspace.
2. Reason about the editing request and decide which tools to call and in what order.
3. Call each tool in sequence. Each tool modifies the image in-place — you do not need to pass file paths.
4. Stop once the request has been fully addressed.

Available tools and when to use them:
- get_image_info     — always call first to inspect the image
- crop               — remove parts of the image or change its aspect ratio
- rotate             — rotate the image clockwise by degrees
- adjust_brightness  — make the image lighter or darker
- adjust_contrast    — increase or decrease tonal range
- adjust_saturation  — boost or mute colors (0=grayscale, 100=unchanged, 200=vivid)
- sharpen            — add crispness/detail
- blur               — soften the image
- grayscale          — convert to black and white
- sepia              — apply a warm vintage tone
- vignette           — darken the edges for a focused look

Be precise and apply only what is needed. Do not call tools whose effects are not asked for.
"""


def _build_message(image_path: str, prompt: str) -> types.Content:
    """Build a multimodal Content message with the image and user prompt."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/jpeg"

    return types.Content(
        role="user",
        parts=[
            types.Part(
                inline_data=types.Blob(mime_type=mime_type, data=image_bytes)
            ),
            types.Part(text=prompt),
        ],
    )


def create_agent() -> LlmAgent:
    model_kwargs: dict = {"model": config.MODEL}
    if config.API_KEY:
        model_kwargs["api_key"] = config.API_KEY
    if config.API_BASE:
        model_kwargs["api_base"] = config.API_BASE
    model = LiteLlm(**model_kwargs)
    return LlmAgent(
        model=model,
        name="image_editor",
        instruction=SYSTEM_PROMPT,
        tools=ALL_TOOLS,
    )


async def run_agent(image_path: str, prompt: str) -> str:
    """Run the agent and return its final text response."""
    agent = create_agent()
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="image_editor",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="image_editor",
        user_id="user",
        session_id="session",
    )

    message = _build_message(image_path, prompt)

    final_response = ""
    try:
        async for event in runner.run_async(
            user_id="user",
            session_id="session",
            new_message=message,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text or ""
    except litellm.AuthenticationError as e:
        raise AuthenticationError(
            f"API authentication failed. Check your Z_AI_API_KEY in .env.\nDetail: {e}"
        ) from e
    except litellm.RateLimitError as e:
        msg = str(e)
        if "balance" in msg.lower() or "recharge" in msg.lower() or "1113" in msg:
            raise InsufficientBalanceError(
                "Insufficient API balance. Please recharge your z.AI account."
            ) from e
        raise AgentError(f"Rate limit exceeded: {e}") from e
    except litellm.BadRequestError as e:
        raise AgentError(f"Bad request to model API: {e}") from e
    except litellm.APIConnectionError as e:
        raise AgentError(f"Could not reach the API at {config.API_BASE}: {e}") from e
    except litellm.APIError as e:
        raise AgentError(f"API error: {e}") from e

    return final_response
