"""
Central configuration for Glassbox's backend.

Everything here is overridable via environment variables (see .env.example),
so the same code runs locally, in Docker, and on whatever host you deploy
the backend to (Render / Fly / Railway - see README for why this is not
Vercel).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_REPO_DIR = BASE_DIR / "sample_repo"

# --- LLM ---
# Glassbox talks to Groq's OpenAI-compatible chat completions API.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")
MAX_TOKENS_PER_CALL = int(os.getenv("MAX_TOKENS_PER_CALL", "2000"))

# --- Context engine ---
# Token budget the context engine is allowed to spend on file contents per
# request. This is the knob that produces the "compression %" stat shown in
# the UI: budget spent / tokens the *whole* repo would have cost.
CONTEXT_TOKEN_BUDGET = int(os.getenv("CONTEXT_TOKEN_BUDGET", "1200"))

# --- Agent loop ---
MAX_REVIEW_ITERATIONS = int(os.getenv("MAX_REVIEW_ITERATIONS", "2"))

# --- CORS ---
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")
