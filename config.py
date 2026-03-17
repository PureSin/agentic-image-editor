import os
from dotenv import load_dotenv

load_dotenv()

# Suppress ADK's warning about using Gemini via LiteLLM — we use LiteLLM
# intentionally so the same code path works for any OpenAI-compatible provider.
os.environ.setdefault("ADK_SUPPRESS_GEMINI_LITELLM_WARNINGS", "true")

API_KEY = os.getenv("API_KEY", "")
API_BASE = os.getenv("API_BASE", "")

# Full LiteLLM model string — include the provider prefix, e.g.:
#   gemini/gemini-3.1-flash-lite-preview   (Google Gemini)
#   openai/GLM-4.6V                        (z.AI)
#   openai/gpt-4o                          (OpenAI)
MODEL = os.getenv("MODEL", "gemini/gemini-3.1-flash-lite-preview")

# Per-agent model overrides — fall back to MODEL if not set
EDITOR_MODEL = os.getenv("EDITOR_MODEL", MODEL)
JUDGE_MODEL = os.getenv("JUDGE_MODEL", MODEL)

MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
