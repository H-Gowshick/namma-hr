"""Score retrieval, answer language, facts, and citations."""

from __future__ import annotations

import re

from services.languages import LANGUAGE_NAMES

SCRIPT_PATTERNS = {
    "en": re.compile(r"[A-Za-z]"),
    "hi": re.compile(r"[\u0900-\u097F]"),
    "mr": re.compile(r"[\u0900-\u097F]"),
    "bn": re.compile(r"[\u0980-\u09FF]"),
    "gu": re.compile(r"[\u0A80-\u0AFF]"),
    "ta": re.compile(r"[\u0B80-\u0BFF]"),
    "te": re.compile(r"[\u0C00-\u0C7F]"),
    "kn": re.compile(r"[\u0C80-\u0CFF]"),
    "ml": re.compile(r"[\u0D00-\u0D7F]"),
}

# "page 2", "p. 2", and the usual word for page in each interface language.
PAGE_RE = re.compile(
    r"(?:"
    r"(?<![A-Za-z])(?:pages?|pg|p\.)"
    r"|पृष्ठ|पेज|पन्ना|पान"
    r"|பக்கம்"
    r"|పేజీ"
    r"|ಪುಟ|ಪೇಜ್"
    r"|પૃ\."
    r"|പേജ്"
    r"|পৃষ্ঠা|পাতা"
    r"|પૃષ્ઠ|પાનું|પેજ"
    r")"
    r"\s*[:#.\-ঃ]?\s*([0-9०-९০-৯]+)",
    re.IGNORECASE,
)
SOURCE_PAGE_RE = re.compile(
    r"HR_POLICY\.pdf(?:(?!HR_POLICY\.pdf).){0,40}?"
    r"(?<![0-9०-९০-৯])([1-4१-४১-৪])(?![0-9०-९০-৯])",
    re.IGNORECASE,
)
DIGIT_TRANSLATION = str.maketrans(
    "०१२३४५६७८९০১২৩৪৫৬৭৮৯૦૧૨૩૪૫૬૭૮૯౦౧౨౩౪౫౬౭౮౯೦೧೨೩೪೫೬೭೮೯൦൧൨൩൪൫൬൭൮൯",
    "0123456789" * 6,
)
DAY_COUNT_RE = re.compile(
    r"(?:"
    r"\b\d+\s*(day|days|week|weeks)\b"
    r"|[०-९]+\s*(दिन|दिवस|आठवडे)"
    r"|[০-৯]+\s*(দিন|সপ্তাহ)"
    r")",
    re.IGNORECASE,
)


def _page_number(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def retrieval_correct(case: dict, results: list[dict]) -> bool:
    """
    In-policy questions pass when a top passage is the expected PDF page
    and contains the expected policy wording.
    Out-of-policy questions pass when the retrieved text does not contain
    the missing topic.
    """

    if not case["in_policy"]:
        absent = (case.get("absent_term") or "").lower()
        combined = "\n".join((item.get("text") or "") for item in results).lower()
        return bool(absent) and absent not in combined

    expected_pages = set(case["expected_pages"])
    terms = [term.lower() for term in case["passage_terms"]]
    matched_text: list[str] = []

    for item in results:
        source = str(item.get("source") or "")
        page = _page_number(item.get("page"))
        text = (item.get("text") or "").lower()

        if case["expected_source"] not in source:
            continue

        if page not in expected_pages:
            continue

        matched_text.append(text)

    combined = "\n".join(matched_text)
    return bool(combined) and all(term in combined for term in terms)


def answer_language_correct(language: str, answer: str) -> bool:
    """
    Hindi and Marathi both use Devanagari, so this check confirms the
    script of the requested language. It does not claim to distinguish
    Hindi from Marathi.
    """

    text = answer or ""
    pattern = SCRIPT_PATTERNS.get(language)

    if pattern is None or not pattern.search(text):
        return False

    if language == "en":
        indic = re.search(
            r"[\u0900-\u097F\u0980-\u09FF\u0A80-\u0AFF\u0B80-\u0BFF"
            r"\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F]",
            text,
        )
        latin = len(re.findall(r"[A-Za-z]", text))
        indic_count = len(indic.group(0)) if indic else 0
        return latin > indic_count

    return True


def _normalized_answer(answer: str) -> str:
    """Map Hindi, Bengali, and other Indic digits to 0-9 before fact checks."""

    return (answer or "").translate(DIGIT_TRANSLATION).lower()


def answer_factually_correct(case: dict, answer: str) -> bool:
    text = answer or ""
    lowered = _normalized_answer(text)

    if not case["in_policy"]:
        refused = any(
            marker.lower() in lowered
            for group in case["answer_any"]
            for marker in group
        )
        invented = bool(DAY_COUNT_RE.search(text) or DAY_COUNT_RE.search(lowered))
        return refused and not invented

    for group in case["answer_any"]:
        if not any(marker.lower() in lowered for marker in group):
            return False

    return True


def _page_int(token: str) -> int | None:
    try:
        return int(str(token).translate(DIGIT_TRANSLATION))
    except ValueError:
        return None


def cited_pages(answer: str) -> set[int]:
    text = answer or ""
    pages: set[int] = set()

    for match in PAGE_RE.findall(text):
        page = _page_int(match)
        if page is not None:
            pages.add(page)

    for match in SOURCE_PAGE_RE.findall(text):
        page = _page_int(match)
        if page is not None:
            pages.add(page)

    return pages


def answer_generated(answer: str | None) -> bool:
    """A Groq failure is not an answer, so it is left unscored."""

    if not answer:
        return False

    lowered = answer.lower()
    return (
        "evaluation error" not in lowered
        and "chat request failed" not in lowered
    )


def citations_correct(case: dict, answer: str) -> bool:
    text = answer or ""
    lowered = text.lower()
    pages_cited = cited_pages(text)
    has_source = "HR_POLICY.pdf" in lowered

    if not case["in_policy"]:
        # A missing topic must not be pinned to a policy page.
        return not pages_cited

    if not has_source:
        return False

    return bool(pages_cited & set(case["expected_pages"]))


def score_case(case: dict, results: list[dict], answer: str | None = None) -> dict:
    retrieved = [
        {
            "source": item.get("source"),
            "page": item.get("page"),
        }
        for item in results
    ]

    row = {
        "language": case["language"],
        "language_name": LANGUAGE_NAMES.get(case["language"], case["language"]),
        "topic": case["topic"],
        "title": case["title"],
        "question": case["question"],
        "expected_facts": case["expected_facts"],
        "expected_source": case["expected_source"],
        "expected_pages": case["expected_pages"],
        "retrieval_returned_correct_source": retrieval_correct(case, results),
        "retrieved_sources": retrieved,
        "answer_used_requested_language": None,
        "answer_factually_correct": None,
        "citations_present_and_correct": None,
        "answer_error": None,
        "answer": answer,
    }

    if answer is not None and not answer_generated(answer):
        row["answer_error"] = "chat_request_failed"
        return row

    if answer is not None:
        row["answer_used_requested_language"] = answer_language_correct(
            case["language"],
            answer,
        )
        row["answer_factually_correct"] = answer_factually_correct(case, answer)
        row["citations_present_and_correct"] = citations_correct(case, answer)

    return row
