"""
Gnani Prisma realtime STT (WebSocket).

Docs: https://docs.gnani.ai/api/STT/stt-websocket
Live microphone should use this path, not the REST batch endpoint.
"""

from __future__ import annotations

import json
import logging

from services.settings import GNANI_API_KEY
from services.stt_languages import (
    build_stt_request_options,
    is_voice_language_supported,
    normalize_app_language,
    unsupported_voice_language_message,
)

logger = logging.getLogger(__name__)

GNANI_STT_WS_URL = "wss://api.vachana.ai/stt/v3/stream"
PCM_FRAME_BYTES = 1024


def build_gnani_stream_headers(language: str | None) -> dict[str, str]:
    api_key = GNANI_API_KEY

    if not api_key:
        raise RuntimeError("GNANI_API_KEY is missing from backend/.env")

    selected = normalize_app_language(language)

    if not is_voice_language_supported(selected):
        raise ValueError(unsupported_voice_language_message(selected))

    options = build_stt_request_options(selected)

    # Headers must stay ASCII-safe for WebSocket clients.
    keyterms = json.dumps(options["keyterms"], ensure_ascii=True)

    return {
        "x-api-key-id": api_key,
        "model": "prisma-v3.0",
        "language_code": str(options["language_code"]),
        "format": str(options["format"]),
        "topic": str(options["topic"]),
        "keyterms": keyterms,
        "x-sample-rate": "16000",
        # Faster end-of-utterance for short HR questions.
        "x-vad-threshold": "0.5",
        "x-min-silence-ms": "400",
        "x-min-speech-ms": "120",
        "x-min-segment-ms": "120",
        "x-max-speech-s": "12",
        "x-idle-timeout-sec": "20",
    }
