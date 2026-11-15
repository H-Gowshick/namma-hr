import hashlib
import logging
import threading
from collections import OrderedDict

import requests

from services.settings import GNANI_API_KEY
from services.tts_text import to_speakable_text
from services.tts_voices import (
    SUPPORTED_GNANI_LANGUAGE_CODES,
    resolve_tts_voice,
)

# =========================================================
# CONFIGURATION
# =========================================================

logger = logging.getLogger(__name__)

GNANI_TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"

DEFAULT_TTS_MODEL = "timbre-v2.5"
# Slightly faster delivery without sounding rushed.
DEFAULT_TTS_SPEED = 1.08
# 22.05 kHz is enough for speech and much faster than 48 kHz WAV.
TTS_SAMPLE_RATE = 22050

REQUEST_TIMEOUT = 45
CACHE_MAX_ITEMS = 32

_session = requests.Session()
_cache_lock = threading.Lock()
_audio_cache: OrderedDict[str, bytes] = OrderedDict()


def _cache_key(text: str, language_code: str, voice: str) -> str:
    digest = hashlib.sha1(
        f"{language_code}|{voice}|{text}".encode("utf-8"),
    ).hexdigest()
    return digest


def _cache_get(key: str) -> bytes | None:
    with _cache_lock:
        audio = _audio_cache.get(key)
        if audio is None:
            return None
        _audio_cache.move_to_end(key)
        return audio


def _cache_put(key: str, audio: bytes) -> None:
    with _cache_lock:
        _audio_cache[key] = audio
        _audio_cache.move_to_end(key)
        while len(_audio_cache) > CACHE_MAX_ITEMS:
            _audio_cache.popitem(last=False)


# =========================================================
# GNANI TIMBRE TEXT-TO-SPEECH
# =========================================================


def synthesize_speech(
    text: str,
    language: str = "en",
    voice: str | None = None,
) -> bytes:
    """
    Convert text into WAV audio using Gnani Timbre v2.5.

    Speaks a cleaned, length-limited version of the answer so
    synthesis stays fast for typical HR replies.
    """

    api_key = GNANI_API_KEY

    if not api_key:
        raise RuntimeError("GNANI_API_KEY is missing from backend/.env")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text cannot be empty.")

    resolved = resolve_tts_voice(language=language, voice=voice)

    if resolved["language_code"] not in SUPPORTED_GNANI_LANGUAGE_CODES:
        raise ValueError(
            f"Unsupported TTS language: {resolved['language_code']}"
        )

    speakable = to_speakable_text(text)

    if not speakable:
        raise ValueError("There is no speakable text in this answer.")

    cache_key = _cache_key(
        speakable,
        resolved["language_code"],
        resolved["voice"],
    )
    cached = _cache_get(cache_key)

    if cached is not None:
        logger.info(
            "Gnani TTS cache hit language=%s voice=%s chars=%s",
            resolved["language_code"],
            resolved["voice"],
            len(speakable),
        )
        return cached

    payload = {
        "text": speakable,
        "voice": resolved["voice"],
        "model": DEFAULT_TTS_MODEL,
        "language": resolved["language_code"],
        "speed": DEFAULT_TTS_SPEED,
        "audio_config": {
            "sample_rate": TTS_SAMPLE_RATE,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav",
        },
    }

    headers = {
        "X-API-Key-ID": api_key,
        "Content-Type": "application/json",
    }

    logger.info(
        "Gnani TTS request language=%s voice=%s chars=%s sample_rate=%s",
        resolved["language_code"],
        resolved["voice"],
        len(speakable),
        TTS_SAMPLE_RATE,
    )

    try:
        response = _session.post(
            GNANI_TTS_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        if not response.ok:
            logger.error(
                "Gnani TTS failed with HTTP status %s",
                response.status_code,
            )

            if response.status_code == 400:
                raise ValueError(
                    "The speech request was rejected. "
                    "Please check the selected language and try again."
                )

            raise RuntimeError(
                f"Gnani TTS service returned HTTP {response.status_code}."
            )

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if "audio/" not in content_type:
            raise RuntimeError(
                "Gnani TTS did not return an audio response. "
                f"Received Content-Type: {content_type or 'unknown'}"
            )

        audio_bytes = response.content

        if not audio_bytes:
            raise RuntimeError("Gnani TTS returned an empty audio response.")

        _cache_put(cache_key, audio_bytes)
        return audio_bytes

    except requests.Timeout as exc:
        raise RuntimeError("Gnani TTS request timed out.") from exc

    except requests.RequestException as exc:
        logger.exception("Gnani TTS network error")

        raise RuntimeError("Could not connect to Gnani TTS.") from exc
