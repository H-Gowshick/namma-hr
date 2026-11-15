"""Shared backend settings. Environment variable names are unchanged."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BACKEND_DIR / ".env", encoding="utf-8-sig")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_FALLBACK_MODELS = os.getenv("GROQ_FALLBACK_MODELS", "openai/gpt-oss-120b")
GNANI_API_KEY = os.getenv("GNANI_API_KEY", "")

_LOCAL_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def _configured_origins() -> list[str]:
    origins: list[str] = []
    for origin in [*_LOCAL_ORIGINS, *os.getenv("CORS_ORIGINS", "").split(",")]:
        cleaned = origin.strip().rstrip("/")
        if cleaned and cleaned not in origins:
            origins.append(cleaned)
    return origins


CORS_ORIGINS = _configured_origins()
