"""
Build English retrieval queries for multilingual HR questions.

Policy PDFs are stored in English. Indic questions are mapped to
focused English search queries without changing the PDF content,
embeddings, or ChromaDB collection.
"""

from __future__ import annotations

import re

from services.languages import language_display_name, normalize_language

NON_LATIN_RE = re.compile(
    r"[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF"
    r"\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF"
    r"\u0D00-\u0D7F\u0600-\u06FF]"
)

LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")

# Observed speech-recognition mixups. "Waternity" was returned for a
# paternity question and then answered as maternity leave.
_LEAVE_MISHEARINGS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bwaternit\w*\b", re.IGNORECASE), "paternity"),
    (re.compile(r"\bpaternat\w*\b", re.IGNORECASE), "paternity"),
    (re.compile(r"\bmaternat\w*\b", re.IGNORECASE), "maternity"),
)


# Each topic has English retrieval queries plus multilingual cues.
# Cues include native-script words and common transliterations.
HR_TOPICS: dict[str, dict] = {
    "casual_leave": {
        "queries": [
            "Casual Leave CL annual entitlement days per year",
            "Casual Leave minimum maximum days carry forward encashment",
        ],
        "cues": [
            "casual leave",
            "casual leaves",
            "cl",
            "आकस्मिक",
            "कैजुअल",
            "कॅज्युअल",
            "ক্যাজুয়াল",
            "કેઝ્યુઅલ",
            "கேஜுவல்",
            "காசுவல்",
            "கேஷுவல்",
            "క్యాజువల్",
            "క్యాజువల",
            "ಕ್ಯಾಶುವಲ್",
            "ಕ್ಯಾಜುಯಲ್",
            "കാഷ്വൽ",
            "കാഷ്വല്",
        ],
    },
    "sick_leave": {
        "queries": [
            "Sick Leave Medical Leave entitlement days certificate",
            "Sick Leave append earned leave pro-rated",
        ],
        "cues": [
            "sick leave",
            "medical leave",
            "sl",
            "बीमार",
            "चिकित्सा",
            "रुग्ण",
            "অসুস্থ",
            "બીમાર",
            "நோய்",
            "மருத்துவ",
            "అనారోగ్య",
            "సిక్",
            "ಅನಾರೋಗ್ಯ",
            "ಸಿಕ್",
            "അസുഖ",
            "സിക്ക്",
        ],
    },
    "earned_leave": {
        "queries": [
            "Earned Leave Privilege Leave EL PL accrual carry forward",
            "Earned Leave every 20 working days 240 days",
        ],
        "cues": [
            "earned leave",
            "privilege leave",
            "privileged leave",
            "el",
            "pl",
            "अर्जित",
            "विशेषाधिकार",
            "एर्न्ड",
            "अर्जित रजा",
            "অর্জিত",
            "કમાયેલ",
            "சம்பாதித்த",
            "பிரிவிலெஜ்",
            "ஈர்ன்ட்",
            "సంపాదిత",
            "ఎర్న్డ్",
            "ಗಳಿಸಿದ",
            "ಎರ್ನ್ಡ್",
            "സമ്പാദ്യ",
            "എര്‍ണ്ഡ്",
        ],
    },
    "carry_forward": {
        "queries": [
            "unused Earned Leave carry forward next calendar year maximum days",
            "Casual Leave no carry forward unused leaves lapse",
        ],
        "cues": [
            "carry forward",
            "carry-forward",
            "carried forward",
            "lapse",
            "unused",
            "आगे ले जा",
            "व्यपगत",
            "క్యారీ ఫార్వర్డ్",
            "கேரி ஃபார்வேர்ட்",
            "ಕ್ಯಾರಿ ಫಾರ್ವರ್ಡ್",
            "ക്യാരി ഫോർവേഡ്",
            "আগে নিয়ে",
            "आगे नेणे",
            "आગળ લઈ",
        ],
    },
    "maternity_leave": {
        "queries": [
            "Maternity Leave weeks entitlement Maternity Benefit Act ESIC",
            "Maternity Leave eligibility 80 days miscarriage",
        ],
        "cues": [
            "maternity",
            "maternity leave",
            "प्रसूति",
            "मैटरनिटी",
            "প্রসূতি",
            "પ્રસૂતિ",
            "மகப்பேறு",
            "మాతృత్వ",
            "ಪ್ರಸೂತಿ",
            "മെറ്റേണിറ്റി",
        ],
    },
    "paternity_leave": {
        "queries": [
            "Paternity leave unpaid male employee child born duration",
            "Paternity leave paid or unpaid policy",
        ],
        "cues": [
            "paternity",
            "paternity leave",
            "पितृत्व",
            "पॅटर्निटी",
            "পিতৃত্ব",
            "પિતૃત્વ",
            "தந்தை",
            "பேட்டர்னிட்டி",
            "పితృత్వ",
            "ಪಿತೃತ್ವ",
            "പാറ്റേണിറ്റി",
        ],
    },
    "approval": {
        "queries": [
            "leave application approval advance casual sick leave manager discretion",
            "apply leave before availing approval required",
        ],
        "cues": [
            "approval",
            "approve",
            "apply",
            "manager",
            "अनुमोदन",
            "मंजूरी",
            "অনুমোদন",
            "મંજૂરી",
            "அனுமதி",
            "ఆమోదం",
            "ಅನುಮೋದನೆ",
            "അനുമതി",
        ],
    },
    "pro_rata": {
        "queries": [
            "pro-rated leave new joiner resigned employees proportion calendar year",
            "prorate leaves half year entitlement",
        ],
        "cues": [
            "pro rata",
            "pro-rata",
            "prorate",
            "prorated",
            "new joiner",
            "resigned",
            "प्रोरेटा",
            "अनुपात",
            "விகிதாசார",
            "ప్రోరేటా",
            "ಪ್ರೋರೇಟ್",
            "പ്രോറാറ്റ",
        ],
    },
    "work_from_home": {
        "queries": [
            "work from home eligible employees case to case basis",
        ],
        "cues": [
            "work from home",
            "wfh",
            "remote",
            "घर से काम",
            "வீட்டிலிருந்து",
            "ఇంటి నుండి",
            "ಮನೆಯಿಂದ",
            "വീട്ടിൽ നിന്ന്",
            "বাড়ি থেকে",
            "घरातून",
            "ઘરેથી",
        ],
    },
    "paid_unpaid": {
        "queries": [
            "paid unpaid half-paid leave Study Leave Bereavement Leave Paternity leave unpaid",
        ],
        "cues": [
            "paid",
            "unpaid",
            "half-paid",
            "encash",
            "encashable",
            "वेतन",
            "बिना वेतन",
            "सம்பள",
            "ஊதியம்",
            "జీతం",
            "ಸಂಬಳ",
            "ശമ്പള",
            "বেতন",
            "पगार",
            "પગાર",
        ],
    },
}


def correct_misheard_leave_terms(text: str) -> str:
    """Map known speech-recognition errors onto the leave type meant."""

    corrected = text or ""

    for pattern, replacement in _LEAVE_MISHEARINGS:
        corrected = pattern.sub(replacement, corrected)

    return corrected


def contains_non_latin_script(text: str) -> bool:
    return bool(NON_LATIN_RE.search(text or ""))


def needs_english_retrieval_query(query: str, language: str | None) -> bool:
    selected = normalize_language(language)

    if selected != "en":
        return True

    return contains_non_latin_script(query)


def is_mostly_english_query(text: str) -> bool:
    """Reject rewrites that still contain Indic script or no Latin words."""

    cleaned = (text or "").strip()

    if not cleaned:
        return False

    if contains_non_latin_script(cleaned):
        return False

    return len(LATIN_WORD_RE.findall(cleaned)) >= 2


def detect_hr_topics(query: str) -> list[str]:
    """Detect leave/policy topics from multilingual cues."""

    lowered = correct_misheard_leave_terms(query or "").lower()
    matched: list[str] = []

    for topic, config in HR_TOPICS.items():
        for cue in config["cues"]:
            if cue.lower() in lowered:
                matched.append(topic)
                break

    return matched


def topic_english_queries(topics: list[str]) -> list[str]:
    queries: list[str] = []

    for topic in topics:
        config = HR_TOPICS.get(topic)
        if not config:
            continue

        for item in config["queries"]:
            if item not in queries:
                queries.append(item)

    return queries


def default_leave_policy_queries() -> list[str]:
    return [
        "leave policy Casual Leave Sick Leave Earned Leave entitlement",
        "leave approval carry forward paid unpaid maternity paternity",
    ]


def build_english_retrieval_queries(
    query: str,
    language: str | None = "en",
    rewritten_query: str | None = None,
) -> list[str]:
    """
    Build one or more English search queries for ChromaDB.

    Priority:
    1. Valid rewritten English query from the LLM
    2. Topic-specific English queries from multilingual cues
    3. Original query when it is already English
    4. Broad leave-policy fallback queries
    """

    original = correct_misheard_leave_terms((query or "").strip())
    selected = normalize_language(language)
    queries: list[str] = []

    rewritten = (rewritten_query or "").strip().strip("\"'` ")

    if rewritten and is_mostly_english_query(rewritten):
        queries.append(rewritten)

    topics = detect_hr_topics(original)
    for item in topic_english_queries(topics):
        if item not in queries:
            queries.append(item)

    if original and is_mostly_english_query(original) and original not in queries:
        queries.insert(0, original)

    if not queries:
        # Selected Indian language with no detected topic and failed rewrite.
        queries.extend(default_leave_policy_queries())

        if selected != "en":
            language_name = language_display_name(selected)
            queries.insert(
                0,
                f"HR leave policy entitlement eligibility approval {language_name}",
            )

    # Keep the list small for latency.
    return queries[:4]


def rewrite_system_prompt() -> str:
    return """
You convert an employee's HR policy question into a short English
search query for English-language HR PDF documents.

Rules:
1. Preserve the original meaning exactly.
2. Keep English HR terms such as Casual Leave, Earned Leave,
   Sick Leave, Privilege Leave, Maternity Leave, and Paternity Leave.
3. Preserve numbers, day limits, dates, and paid/unpaid conditions.
4. Prefer concrete policy terms: entitlement, eligibility,
   carry forward, approval, pro-rata, encashment.
5. Output only the English search query.
6. Do not answer the question.
7. Do not invent policy facts.
8. Never change paternity into maternity, or maternity into paternity.
   "Waternity" means paternity leave.
""".strip()
