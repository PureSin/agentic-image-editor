import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
# Full LiteLLM model string — include the provider prefix, e.g.:
#   gemini/gemini-2.5-flash-lite-preview   (Google Gemini)
#   openai/GLM-4.6V                        (z.AI)
#   openai/gpt-4o                          (OpenAI)
MODEL = os.getenv("MODEL", "gemini/gemini-2.5-flash-lite-preview")
API_BASE = os.getenv("API_BASE", "")
