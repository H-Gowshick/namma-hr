import json
import logging
from pathlib import Path

import requests

from services.settings import GNANI_API_KEY
from services.stt_languages import (
    build_stt_request_options,
    is_voice_language_supported,
    language_mismatch_message,
    normalize_app_language,
    transcript_matches_language,
    unsupported_voice_language_message,
)

logger = logging.getLogger(__name__)

GNANI_API_URL = "https://api.vachana.ai/stt/v3"
REQUEST_TIMEOUT = 20

# Reuse TLS connections across transcription requests.
_session = requests.Session()

SUPPORTED_AUDIO_TYPES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
}

MIN_AUDIO_BYTES = 1000


def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "recording.wav",
    language: str = "en",
) -> dict:
    """
    Convert recorded speech into text using Gnani Prisma v3.

    language is an app UI code such as en, hi, ta.
    The request uses only that language, so the transcript is
    written in the selected language.
    """

    api_key = GNANI_API_KEY

    if not api_key:
        raise RuntimeError("GNANI_API_KEY is missing from backend/.env")

    selected_language = normalize_app_language(language)

    if not is_voice_language_supported(selected_language):
        raise ValueError(unsupported_voice_language_message(selected_language))

    if not audio_bytes:
        raise ValueError("No audio was recorded. Please try recording again.")

    if len(audio_bytes) < MIN_AUDIO_BYTES:
        raise ValueError(
            "The recording is too short. Please speak for a little longer."
        )

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_AUDIO_TYPES:
        raise ValueError(
            f"Unsupported audio format: {extension}. "
            f"Supported formats: {', '.join(SUPPORTED_AUDIO_TYPES)}"
        )

    content_type = SUPPORTED_AUDIO_TYPES[extension]
    stt_options = build_stt_request_options(selected_language)

    headers = {
        "X-API-Key-ID": api_key,
    }

    data = {
        "model": "prisma-v3.0",
        "language_code": stt_options["language_code"],
        "format": stt_options["format"],
        "topic": stt_options["topic"],
        "keyterms": json.dumps(stt_options["keyterms"], ensure_ascii=False),
    }

    files = {
        "audio_file": (
            filename,
            audio_bytes,
            content_type,
        ),
    }

    logger.info(
        "Gnani STT request language=%s language_code=%s format=%s bytes=%s",
        selected_language,
        stt_options["language_code"],
        stt_options["format"],
        len(audio_bytes),
    )

    try:
        response = _session.post(
            GNANI_API_URL,
            headers=headers,
            data=data,
            files=files,
            timeout=REQUEST_TIMEOUT,
        )

        if not response.ok:
            # Never log response bodies that might contain secrets.
            logger.error(
                "Gnani STT failed with HTTP %s",
                response.status_code,
            )

            if response.status_code == 400:
                raise ValueError(
                    "The audio or language setting was rejected by speech "
                    "recognition. Please try again."
                )

            raise RuntimeError(
                f"Gnani STT service returned HTTP {response.status_code}."
            )

        try:
            result = response.json()
        except ValueError as exc:
            raise RuntimeError("Gnani returned an invalid response.") from exc

    except requests.Timeout as exc:
        logger.warning("Gnani STT request timed out.")
        raise RuntimeError(
            "Speech recognition timed out. Please try again."
        ) from exc

    except requests.RequestException as exc:
        logger.exception("Gnani STT network error.")
        raise RuntimeError(
            "Could not connect to Gnani speech recognition."
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError("Gnani returned an unexpected response.")

    if not result.get("success"):
        logger.warning("Gnani transcription was unsuccessful.")
        raise ValueError(
            "Speech could not be recognized. Please speak clearly and try again."
        )

    transcript = result.get("transcript") or ""

    if not isinstance(transcript, str) or not transcript.strip():
        logger.info("Gnani returned no recognized speech.")
        raise ValueError("No speech was detected. Please try recording again.")

    transcript = transcript.strip()
    detected_language = result.get("detected_language_code")

    if not transcript_matches_language(transcript, selected_language):
        logger.info(
            "STT script mismatch language=%s detected=%s",
            selected_language,
            detected_language,
        )
        raise ValueError(
            language_mismatch_message(selected_language, detected_language)
        )

    return {
        "transcript": transcript,
        "detected_language": result.get("detected_language_code"),
        "requested_language": selected_language,
        "language_code": stt_options["language_code"],
        "format": stt_options["format"],
        "model": result.get("model"),
        "processing_time": result.get("processing_time"),
    }
