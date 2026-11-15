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

SUPPORTED_LANGUAGES: tuple[AppLanguageCode, ...] = (
    "en",
    "hi",
    "ta",
    "te",
    "kn",
    "ml",
    "bn",
    "mr",
    "gu",
)

DEFAULT_LANGUAGE: AppLanguageCode = "en"

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
}


def normalize_language(language: str | None) -> AppLanguageCode:
    if language in LANGUAGE_NAMES:
        return language  # type: ignore[return-value]

    return DEFAULT_LANGUAGE


def language_display_name(language: str | None) -> str:
    return LANGUAGE_NAMES.get(
        normalize_language(language),
        "English",
    )


def language_instruction(language: str | None) -> str:
    code = normalize_language(language)
    name = language_display_name(code)

    return f"""
RESPONSE LANGUAGE OVERRIDE:

The employee selected {name} in the language selector.
Answer the entire response in natural {name}.
This rule wins over the language of the question.
Do this even when the question, or some HR terms inside it, are in English.
Do not switch the answer to English unless {name} is English.
Preserve important English HR terms such as Casual Leave,
Earned Leave, Sick Leave, Maternity Leave, and Paternity Leave.
Paternity Leave and Maternity Leave are different. Never answer
one of them with the other's rules.
Keep source filenames and page numbers in their original form.
Do not mix unrelated languages in the answer.
""".strip()
