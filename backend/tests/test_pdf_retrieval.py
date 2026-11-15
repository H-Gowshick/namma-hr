"""
Retrieval tests for English and multilingual HR questions.

These tests use the existing ChromaDB index and embedding model.
Indic questions are converted to English search queries first;
PDF content and metadata stay unchanged.
"""

from services.retrieval.pdf_retrieval import retrieve, retrieve_multi
from services.hr_query_normalization import build_english_retrieval_queries


ENGLISH_QUESTIONS = [
    "How many casual leave days can an employee take?",
    "Can unused earned leave be carried forward?",
    "How many days of maternity leave are provided?",
    "What is the rule for sick leave?",
    "Is paternity leave paid?",
    "Can casual leave be combined with sick leave?",
    "What is the company's policy on work from home?",
    "What is the company's travel reimbursement policy?",
]


# language, question, substrings that should appear in top passages
MULTILINGUAL_CASES = [
    (
        "en",
        "How many casual leave days can an employee take?",
        ["casual leave"],
    ),
    (
        "ta",
        "ஒரு ஊழியருக்கு வருடத்திற்கு எத்தனை கேஷுவல் லீவு கிடைக்கும்?",
        ["casual leave"],
    ),
    (
        "hi",
        "मुझे एक साल में कितनी कैजुअल लीव मिलती है?",
        ["casual leave"],
    ),
    (
        "kn",
        "ನನಗೆ ವರ್ಷಕ್ಕೆ ಎಷ್ಟು ಕ್ಯಾಶುವಲ್ ಲೀವ್ ಸಿಗುತ್ತದೆ?",
        ["casual leave"],
    ),
    (
        "te",
        "ఒక ఉద్యోగికి సంవత్సరానికి ఎన్ని క్యాజువల్ లీవ్‌లు ఉంటాయి?",
        ["casual leave"],
    ),
    (
        "ml",
        "ഒരു ജീവനക്കാരന് വർഷത്തിൽ എത്ര കാഷ്വൽ ലീവ് ലഭിക്കും?",
        ["casual leave"],
    ),
    (
        "bn",
        "একজন কর্মচারী বছরে কতদিন ক্যাজুয়াল ছুটি পান?",
        ["casual leave"],
    ),
    (
        "mr",
        "मला वर्षभरात किती कॅज्युअल रजा मिळतात?",
        ["casual leave"],
    ),
    (
        "gu",
        "મને વર્ષમાં કેટલી કેઝ્યુઅલ રજા મળે છે?",
        ["casual leave"],
    ),
    (
        "hi",
        "क्या अप्रयुक्त अर्जित छुट्टी अगले वर्ष आगे ले जाई जा सकती है?",
        ["earned leave", "carry"],
    ),
    (
        "ta",
        "பேட்டர்னிட்டி லீவ் சம்பளத்துடன் கூடியதா?",
        ["paternity"],
    ),
    (
        "kn",
        "ಸಿಕ್ ಲೀವ್ ನಿಯಮ ಏನು?",
        ["sick leave"],
    ),
]


def print_results(label: str, results: list[dict]) -> None:
    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)

    if not results:
        print("No results.")
        return

    for rank, result in enumerate(results, start=1):
        print(f"\nResult {rank}")
        print("Source:", result["source"])
        print("Page:", result["page"])
        print("Heading:", result["heading"])
        print("Semantic:", round(result["similarity"], 4))
        print("Keyword:", round(result["keyword_score"], 4))
        print("Combined:", round(result["relevance_score"], 4))
        if result.get("matched_query"):
            print("Matched query:", result["matched_query"])
        print("Text:")
        print(result["text"])


def assert_expected_terms(results: list[dict], expected_terms: list[str]) -> None:
    combined = " ".join(item["text"] for item in results).lower()

    missing = [term for term in expected_terms if term.lower() not in combined]

    if missing:
        raise AssertionError(
            "Expected terms not found in retrieved passages: "
            + ", ".join(missing)
        )

    for item in results:
        if not item.get("source"):
            raise AssertionError("Retrieved passage is missing source metadata.")
        if item.get("page") in (None, ""):
            raise AssertionError("Retrieved passage is missing page metadata.")


def run_english_smoke_tests() -> None:
    print("\nENGLISH RETRIEVAL SMOKE TESTS")

    for question in ENGLISH_QUESTIONS:
        results = retrieve(question, top_k=3)
        print_results(f"QUESTION: {question}", results)

        if not results:
            raise AssertionError(f"No English retrieval results for: {question}")

        for item in results:
            if not item.get("source"):
                raise AssertionError("Missing source on English retrieval result.")
            if item.get("page") in (None, ""):
                raise AssertionError("Missing page on English retrieval result.")


def run_multilingual_tests() -> None:
    print("\nMULTILINGUAL RETRIEVAL TESTS")

    for language, question, expected_terms in MULTILINGUAL_CASES:
        queries = build_english_retrieval_queries(
            query=question,
            language=language,
            rewritten_query=None,
        )

        results = retrieve_multi(queries, top_k=4)

        print_results(
            f"LANGUAGE={language} | QUESTION={question}\nQUERIES={queries}",
            results,
        )

        if not results:
            raise AssertionError(
                f"No multilingual retrieval results for [{language}]: {question}"
            )

        assert_expected_terms(results, expected_terms)


if __name__ == "__main__":
    run_english_smoke_tests()
    run_multilingual_tests()
    print("\nAll retrieval tests passed.")
