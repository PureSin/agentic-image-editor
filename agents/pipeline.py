"""Orchestrates the editor→judge loop using ADK's LoopAgent."""

import litellm
from google.adk.agents import LoopAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

import config
from agent import AgentError, AuthenticationError, InsufficientBalanceError
from agents.editor import create_editor
from agents.judge import create_judge


def create_pipeline(max_iterations: int) -> LoopAgent:
    editor = create_editor(config.EDITOR_MODEL, config.API_KEY, config.API_BASE)
    judge = create_judge(config.JUDGE_MODEL, config.API_KEY, config.API_BASE)

    return LoopAgent(
        name="edit_pipeline",
        sub_agents=[editor, judge],
        max_iterations=max_iterations,
    )


async def run_pipeline(
    original_image_path: str,
    working_image_path: str,
    prompt: str,
    max_iterations: int,
    target_iterations: int | None,
) -> str:
    """Run the editor→judge loop and return the final agent summary."""
    pipeline = create_pipeline(max_iterations)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=pipeline,
        app_name="image_editor",
        session_service=session_service,
    )

    initial_state = {
        "original_image_path": original_image_path,
        "working_image_path": working_image_path,
        "prompt": prompt,
        "feedback": "",
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "target_iterations": target_iterations,
    }

    await session_service.create_session(
        app_name="image_editor",
        user_id="user",
        session_id="session",
        state=initial_state,
    )

    # Initial message: image + prompt for the editor's first pass
    with open(original_image_path, "rb") as f:
        image_bytes = f.read()
    import mimetypes
    mime_type = mimetypes.guess_type(original_image_path)[0] or "image/jpeg"
    message = types.Content(
        role="user",
        parts=[
            types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_bytes)),
            types.Part(text=prompt),
        ],
    )

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
            f"API authentication failed. Check your API_KEY in .env.\nDetail: {e}"
        ) from e
    except litellm.RateLimitError as e:
        msg = str(e)
        if "balance" in msg.lower() or "recharge" in msg.lower() or "1113" in msg:
            raise InsufficientBalanceError(
                "Insufficient API balance. Please recharge your account."
            ) from e
        raise AgentError(f"Rate limit exceeded: {e}") from e
    except litellm.BadRequestError as e:
        raise AgentError(f"Bad request to model API: {e}") from e
    except litellm.APIConnectionError as e:
        raise AgentError(f"Could not reach the API at {config.API_BASE}: {e}") from e
    except litellm.APIError as e:
        raise AgentError(f"API error: {e}") from e

    return final_response
