"""
Gnani Prisma STT language mapping.

Source: https://docs.gnani.ai/api/STT/models/prisma-v3
and https://docs.gnani.ai/api/STT/languages

Prisma v3.0 language_code is a hint. Sending one code makes the
model listen for that language first. `format=verbatim` writes
Indic speech in its native script. `format=transcribe` is the
documented style for English.

Odia and Urdu are not in the Prisma language list and are not
offered in the app.
"""

from __future__ import annotations

import re
from typing import Literal

AppLanguageCode = Literal[
    "en",
    "hi",
    "ta",
    "te",
    "kn",
    "ml",
    "bn",
    "mr",
    "gu",
]

# Confirmed Prisma language codes from Gnani docs.
GNANI_STT_CODES: dict[str, str] = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
}

# Kept so an old client that still sends these codes gets a clear
# error instead of an English transcript.
UNSUPPORTED_VOICE_LANGUAGES: dict[str, str] = {
    "or": "Odia",
    "ur": "Urdu",
}

LANGUAGE_DISPLAY_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "or": "Odia",
    "ur": "Urdu",
}

# Native-script check. Hindi and Marathi both use Devanagari.
SCRIPT_PATTERNS: dict[str, re.Pattern[str]] = {
    "hi": re.compile(r"[\u0900-\u097F]"),
    "mr": re.compile(r"[\u0900-\u097F]"),
    "bn": re.compile(r"[\u0980-\u09FF]"),
    "gu": re.compile(r"[\u0A80-\u0AFF]"),
    "ta": re.compile(r"[\u0B80-\u0BFF]"),
    "te": re.compile(r"[\u0C00-\u0C7F]"),
    "kn": re.compile(r"[\u0C80-\u0CFF]"),
    "ml": re.compile(r"[\u0D00-\u0D7F]"),
}

LATIN_LETTERS = re.compile(r"[A-Za-z]")

# Short HR hints. Native words are ones already used by retrieval.
# Gnani docs: keyterms improve recognition and should not insert
# words that were not spoken.
STT_TOPIC = (
    "An employee is asking an HR leave-policy question, including "
    "whether paternity leave or maternity leave is paid or unpaid."
)

SHARED_KEYTERMS = (
    "paternity leave",
    "maternity leave",
    "casual leave",
    "sick leave",
    "earned leave",
    "paid",
    "unpaid",
)

NATIVE_KEYTERMS: dict[str, tuple[str, ...]] = {
    "hi": ("पितृत्व", "प्रसूति", "आकस्मिक", "बीमार", "अर्जित"),
    "ta": ("தந்தை", "பேட்டர்னிட்டி", "மகப்பேறு", "கேஷுவல்", "நோய்"),
    "te": ("పితృత్వ", "మాతృత్వ", "క్యాజువల్", "అనారోగ్య", "సంపాదిత"),
    "kn": ("ಪಿತೃತ್ವ", "ಪ್ರಸೂತಿ", "ಕ್ಯಾಶುವಲ್", "ಅನಾರೋಗ್ಯ", "ಗಳಿಸಿದ"),
    "ml": ("പാറ്റേണിറ്റി", "മെറ്റേണിറ്റി", "കാഷ്വൽ", "അസുഖ", "സമ്പാദ്യ"),
    "bn": ("পিতৃত্ব", "প্রসূতি", "ক্যাজুয়াল", "অসুস্থ", "অর্জিত"),
    "mr": ("पॅटर्निटी", "पितृत्व", "प्रसूति", "कॅज्युअल", "रुग्ण"),
    "gu": ("પિતૃત્વ", "પ્રસૂતિ", "કેઝ્યુઅલ", "બીમાર", "કમાયેલ"),
}


def normalize_app_language(language: str | None) -> str:
    if not language:
        return "en"

    code = language.strip().lower()

    if code in GNANI_STT_CODES or code in UNSUPPORTED_VOICE_LANGUAGES:
        return code

    for app_code, gnani_code in GNANI_STT_CODES.items():
        if code == gnani_code.lower():
            return app_code

    return "en"


def is_voice_language_supported(language: str | None) -> bool:
    code = normalize_app_language(language)
    return code in GNANI_STT_CODES


def unsupported_voice_language_message(language: str | None) -> str:
    code = normalize_app_language(language)
    name = UNSUPPORTED_VOICE_LANGUAGES.get(
        code,
        LANGUAGE_DISPLAY_NAMES.get(code, code),
    )

    supported = ", ".join(
        LANGUAGE_DISPLAY_NAMES[item] for item in GNANI_STT_CODES
    )

    return (
        f"Voice input is not available for {name}. "
        f"Gnani Prisma currently supports: {supported}. "
        "Please choose a supported language or type your question."
    )


def build_stt_request_options(language: str | None) -> dict[str, str | list[str]]:
    """
    Build Prisma fields for the language selected in the UI.

    One language code only. Indic output uses verbatim so the
    transcript stays in that language's script.
    """

    code = normalize_app_language(language)

    if code in UNSUPPORTED_VOICE_LANGUAGES:
        raise ValueError(unsupported_voice_language_message(code))

    gnani_code = GNANI_STT_CODES[code]
    keyterms = list(SHARED_KEYTERMS)
    keyterms.extend(NATIVE_KEYTERMS.get(code, ()))

    return {
        "language_code": gnani_code,
        "format": "transcribe" if code == "en" else "verbatim",
        "topic": STT_TOPIC,
        "keyterms": keyterms,
    }


def transcript_matches_language(transcript: str, language: str | None) -> bool:
    """
    True when the transcript is written in the selected language.

    Indic selections require that script. A few Latin HR words are
    allowed beside it. English requires Latin letters.
    """

    text = transcript or ""
    code = normalize_app_language(language)

    if code == "en":
        return bool(LATIN_LETTERS.search(text))

    pattern = SCRIPT_PATTERNS.get(code)

    if pattern is None:
        return False

    return bool(pattern.search(text))


def language_mismatch_message(
    language: str | None,
    detected_language: str | None = None,
) -> str:
    code = normalize_app_language(language)
    selected_name = LANGUAGE_DISPLAY_NAMES.get(code, code)

    heard_name = None

    if detected_language:
        detected = detected_language.strip().lower()

        for app_code, gnani_code in GNANI_STT_CODES.items():
            if detected in {app_code, gnani_code.lower()}:
                heard_name = LANGUAGE_DISPLAY_NAMES[app_code]
                break

    if heard_name and heard_name != selected_name:
        heard = f"recognized as {heard_name}, not {selected_name}"
    else:
        heard = f"not recognized as {selected_name}"

    return (
        f"This recording was {heard}. "
        f"Please speak your question in {selected_name} and try again. "
        "Nothing was sent to the assistant."
    )
