"""
Lab 11 — Configuration & API Key Setup
"""
import os
from pathlib import Path

from dotenv import load_dotenv


def setup_api_key():
    """Load a local API key when present without blocking offline policy work."""
    repo_env = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(repo_env)
    if "GOOGLE_API_KEY" not in os.environ:
        print(
            "GOOGLE_API_KEY not configured — offline policy tests can run, "
            "but live Gemini agent parts will be skipped or report errors."
        )
        return False
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"
    print("API key loaded.")
    return True


# Allowed banking topics (used by topic_filter)
ALLOWED_TOPICS = [
    "banking", "account", "transaction", "transfer",
    "loan", "interest", "savings", "credit",
    "deposit", "withdrawal", "balance", "payment",
    "tai khoan", "giao dich", "tiet kiem", "lai suat",
    "chuyen tien", "the tin dung", "so du", "vay",
    "ngan hang", "atm",
]

# Blocked topics (immediate reject)
BLOCKED_TOPICS = [
    "hack", "exploit", "weapon", "drug", "illegal",
    "violence", "gambling", "bomb", "kill", "steal",
]
