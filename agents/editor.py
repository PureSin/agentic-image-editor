"""Editor agent — applies ImageMagick tools to fulfill the editing request."""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from tools import ALL_TOOLS

EDITOR_INSTRUCTION = """\
You are an expert image editing agent with access to ImageMagick-powered tools.

Your workflow:
1. Call get_image_info() to understand the current image dimensions, format, and colorspace.
2. Reason about the editing request and plan which tools to apply and in what order.
3. Call each tool in sequence. Tools modify the image in-place — do not pass file paths.
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

If there is feedback from a previous judge evaluation visible in the conversation history,
incorporate it carefully. Focus on what the judge said was wrong and adjust accordingly.

Be precise — apply only the tools needed to fulfill the request.
"""


def create_editor(model_str: str, api_key: str, api_base: str) -> LlmAgent:
    model_kwargs: dict = {"model": model_str}
    if api_key:
        model_kwargs["api_key"] = api_key
    if api_base:
        model_kwargs["api_base"] = api_base

    return LlmAgent(
        name="editor",
        model=LiteLlm(**model_kwargs),
        instruction=EDITOR_INSTRUCTION,
        tools=ALL_TOOLS,
    )
