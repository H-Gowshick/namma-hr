"""
Central Gnani Timbre v2.5 TTS voice mapping.

Voice catalog source:
https://docs.gnani.ai/api/TTS/available-voices

This project already verified:
- English -> Pranav + en-IN
- Tamil   -> Nalini + ta-IN

Odia and Urdu are not offered. They are not in the Timbre catalog.
"""

from __future__ import annotations

from typing import TypedDict


class TtsVoiceConfig(TypedDict):
    language_code: str
    voice: str
    english_name: str


# Preferred voices chosen only from the official Timbre v2.5 catalog.
# English and Tamil keep the already-tested project voices.
TTS_VOICE_MAP: dict[str, TtsVoiceConfig] = {
    "en": {
        "language_code": "en-IN",
        "voice": "Pranav",
        "english_name": "English",
    },
    "hi": {
        "language_code": "hi-IN",
        "voice": "Deepak",
        "english_name": "Hindi",
    },
    "ta": {
        "language_code": "ta-IN",
        "voice": "Nalini",
        "english_name": "Tamil",
    },
    "te": {
        "language_code": "te-IN",
        "voice": "Suhana",
        "english_name": "Telugu",
    },
    "kn": {
        "language_code": "kn-IN",
        "voice": "Saanvi",
        "english_name": "Kannada",
    },
    "ml": {
        "language_code": "ml-IN",
        "voice": "Reshma",
        "english_name": "Malayalam",
    },
    "bn": {
        "language_code": "bn-IN",
        "voice": "Kirra",
        "english_name": "Bengali",
    },
    "mr": {
        "language_code": "mr-IN",
        "voice": "Zahira",
        "english_name": "Marathi",
    },
    "gu": {
        "language_code": "gu-IN",
        "voice": "Falak",
        "english_name": "Gujarati",
    },
}

UNSUPPORTED_TTS_LANGUAGES: dict[str, str] = {
    "or": "Odia",
    "ur": "Urdu",
}

SUPPORTED_GNANI_LANGUAGE_CODES = {
    config["language_code"] for config in TTS_VOICE_MAP.values()
}

SUPPORTED_VOICES = {config["voice"] for config in TTS_VOICE_MAP.values()}


def normalize_tts_language(language: str | None) -> str:
    if not language:
        return "en"

    code = language.strip()

    if code in TTS_VOICE_MAP or code in UNSUPPORTED_TTS_LANGUAGES:
        return code

    lowered = code.lower()

    for app_code, config in TTS_VOICE_MAP.items():
        if lowered == app_code or lowered == config["language_code"].lower():
            return app_code

    # Legacy locale-only requests from older frontend builds.
    if lowered == "ta-in":
        return "ta"
    if lowered == "en-in":
        return "en"

    return "en"


def is_tts_language_supported(language: str | None) -> bool:
    code = normalize_tts_language(language)
    return code in TTS_VOICE_MAP


def unsupported_tts_language_message(language: str | None) -> str:
    code = normalize_tts_language(language)
    name = UNSUPPORTED_TTS_LANGUAGES.get(
        code,
        code,
    )
    supported = ", ".join(
        config["english_name"] for config in TTS_VOICE_MAP.values()
    )

    return (
        f"Voice output is not available for {name} yet. "
        f"Supported spoken languages: {supported}. "
        "You can still read the text answer."
    )


def resolve_tts_voice(
    language: str | None,
    voice: str | None = None,
) -> TtsVoiceConfig:
    """
    Resolve Timbre language + voice for an app language selection.

    If an explicit voice is provided, it must be one of the verified
    mapped voices for the selected language (or the language default).
    """

    code = normalize_tts_language(language)

    if code in UNSUPPORTED_TTS_LANGUAGES:
        raise ValueError(unsupported_tts_language_message(code))

    config = TTS_VOICE_MAP[code]
    selected_voice = (voice or "").strip() or config["voice"]

    # Allow the language's configured voice only. Do not invent others.
    allowed_for_language = {config["voice"]}

    # Preserve older clients that still send Pranav/Nalini with locales.
    if code == "en":
        allowed_for_language.add("Pranav")
    if code == "ta":
        allowed_for_language.add("Nalini")

    if selected_voice not in allowed_for_language:
        raise ValueError(
            f"Voice '{selected_voice}' is not configured for "
            f"{config['english_name']}. Use '{config['voice']}'."
        )

    return {
        "language_code": config["language_code"],
        "voice": selected_voice,
        "english_name": config["english_name"],
    }
