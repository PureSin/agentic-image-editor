"""Judge agent — evaluates the edited image and either accepts or requests refinement."""

# TODO: Polish judge agent and build a proper eval set
#
# Evaluation set ideas:
#   - Collect a corpus of (input_image, prompt, expected_output) triples covering
#     each tool: crop, rotate, grayscale, sepia, brightness, contrast, saturation,
#     sharpen, blur, vignette — plus multi-step combinations.
#   - Define scoring rubrics per edit type (e.g. correct aspect ratio for crops,
#     perceptual similarity for filter strength, correct orientation for rotations).
#   - Add an automated eval runner that scores judge accept/reject decisions against
#     ground-truth labels so we can tune the judge prompt without manual review.
#   - Consider a stricter judge prompt variant and a lenient one — measure which
#     produces better final outputs across the eval set.
#   - Track judge feedback quality: does the feedback actually lead to a better
#     result on the next iteration? Use this to refine the feedback prompt.
#   - Explore using a stronger model (e.g. gemini-3.1-pro or claude-opus) as judge
#     while keeping a lighter model for the editor to balance cost vs quality.

import mimetypes

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from tools import state as tool_state

JUDGE_INSTRUCTION = """\
You are an image editing quality judge. You will be shown the original image and the \
edited image side by side, along with the original editing prompt.

Your job:
1. Compare the edited image against what the prompt asked for.
2. Decide: does the edit satisfactorily fulfill the prompt?

If YES — call exit_loop() to accept the result and end the process.
If NO  — call provide_feedback(feedback) with specific, actionable feedback for the editor.

If the conversation indicates that the target or maximum number of iterations has been \
reached, you MUST call exit_loop() regardless of quality — accept the best result so far.

Feedback guidelines:
- Be specific: name exactly which tools should be applied differently (e.g. "the image \
needs more contrast — try adjust_contrast with a higher value").
- Be concise: one or two sentences of clear direction.
- Do not repeat feedback that was already tried unsuccessfully.
"""


# ── Judge tools ──────────────────────────────────────────────────────────────

def exit_loop(tool_context: ToolContext) -> str:
    """Accept the current edited image and end the editing loop."""
    tool_context.actions.escalate = True
    return "Edit accepted. Loop complete."


def provide_feedback(feedback: str, tool_context: ToolContext) -> str:
    """Record feedback for the editor to act on in the next iteration.

    Args:
        feedback: Specific, actionable instruction describing what the editor should
                  change on the next attempt.
    """
    tool_context.state["feedback"] = feedback
    return f"Feedback recorded: {feedback}"


# ── Callback: inject both images before judge runs ───────────────────────────

def _load_image_part(path: str) -> types.Part:
    with open(path, "rb") as f:
        data = f.read()
    mime_type = mimetypes.guess_type(path)[0] or "image/jpeg"
    return types.Part(inline_data=types.Blob(mime_type=mime_type, data=data))


def before_judge_callback(callback_context: CallbackContext) -> types.Content | None:
    """Inject the original + edited images and update iteration tracking."""
    # Advance iteration counter in both session state and tool_state
    count = callback_context.state.get("iteration_count", 0) + 1
    callback_context.state["iteration_count"] = count
    tool_state.set_iteration(count)

    original_path = callback_context.state.get("original_image_path", "")
    working_path = callback_context.state.get("working_image_path", "")
    prompt = callback_context.state.get("prompt", "")
    target = callback_context.state.get("target_iterations")
    max_iter = callback_context.state.get("max_iterations")

    parts: list[types.Part] = []

    # Original image
    parts.append(_load_image_part(original_path))
    parts.append(types.Part(text="[Original image]"))

    # Edited image (current working state)
    parts.append(_load_image_part(working_path))
    parts.append(types.Part(text="[Edited image]"))

    # Evaluation context
    hit_target = target is not None and count >= target
    hit_max = max_iter is not None and count >= max_iter
    force_accept = hit_target or hit_max

    instruction_parts = [
        f"Editing prompt: \"{prompt}\"",
        f"Iteration: {count}",
    ]
    if force_accept:
        instruction_parts.append(
            f"Iteration limit reached ({count}). You MUST call exit_loop() now."
        )
    else:
        instruction_parts.append(
            "Evaluate whether the edited image satisfactorily fulfills the prompt."
        )

    parts.append(types.Part(text="\n".join(instruction_parts)))

    return types.Content(role="user", parts=parts)


# ── Factory ───────────────────────────────────────────────────────────────────

def create_judge(model_str: str, api_key: str, api_base: str) -> LlmAgent:
    model_kwargs: dict = {"model": model_str}
    if api_key:
        model_kwargs["api_key"] = api_key
    if api_base:
        model_kwargs["api_base"] = api_base

    return LlmAgent(
        name="judge",
        model=LiteLlm(**model_kwargs),
        instruction=JUDGE_INSTRUCTION,
        tools=[exit_loop, provide_feedback],
        before_agent_callback=before_judge_callback,
    )
