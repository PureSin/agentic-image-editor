import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("Z_AI_API_KEY", "")
MODEL = os.getenv("MODEL", "GLM-4.6V")
API_BASE = os.getenv("API_BASE", "https://api.z.ai/api/paas/v4/")
