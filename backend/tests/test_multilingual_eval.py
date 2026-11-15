"""
Evaluation checks that do not call Groq or Gnani.

Retrieval uses the local Chroma index. Voice checks use the configured
Gnani language and voice map. Full answer scoring is
`python -m evaluation.run_multilingual_eval --answers`.
"""

from evaluation.cases import LANGUAGES, TOPICS, evaluation_cases
from evaluation.run_multilingual_eval import (
    evaluate_retrieval,
    voice_rows,
    write_report,
)
from evaluation.score import (
    answer_factually_correct,
    answer_language_correct,
    citations_correct,
)
from services.stt_languages import build_stt_request_options
from services.tts_voices import resolve_tts_voice


def test_dataset_covers_every_interface_language_and_topic():
    rows = evaluation_cases()

    assert len(LANGUAGES) == 9
    assert len(TOPICS) == 10
    assert len(rows) == 90

    covered = {(row["language"], row["topic"]) for row in rows}
    expected = {
        (language, topic["id"])
        for language in LANGUAGES
        for topic in TOPICS
    }

    assert covered == expected

    for row in rows:
        assert row["question"].strip()
        assert row["expected_facts"].strip()


def test_answer_scoring_examples():
    tamil = {
        "language": "ta",
        "in_policy": True,
        "expected_pages": [1, 2],
        "answer_any": [["7"]],
    }
    tamil_answer = (
        "கேஷுவல் லீவ் ஆண்டுக்கு 7 நாள். "
        "(Source: HR_POLICY.pdf, page 1)"
    )

    assert answer_language_correct("ta", tamil_answer)
    assert answer_factually_correct(tamil, tamil_answer)
    assert citations_correct(tamil, tamil_answer)

    missing = {
        "language": "en",
        "in_policy": False,
        "expected_pages": [],
        "answer_any": [["not found"]],
    }
    missing_answer = (
        "Adoption leave was not found in the available policy documents."
    )

    assert answer_language_correct("en", missing_answer)
    assert answer_factually_correct(missing, missing_answer)
    assert citations_correct(missing, missing_answer)

    invented = "Adoption leave is 15 days. (Source: HR_POLICY.pdf, page 2)"
    assert not answer_factually_correct(missing, invented)
    assert not citations_correct(missing, invented)

    bengali_digits = {
        "language": "bn",
        "in_policy": True,
        "expected_pages": [3],
        "answer_any": [["45"]],
    }
    assert answer_factually_correct(
        bengali_digits,
        "সর্বোচ্চ সীমা ৪৫ দিন। HR_POLICY.pdf পৃষ্ঠা ৩",
    )
    assert citations_correct(
        bengali_digits,
        "সর্বোচ্চ সীমা ৪৫ দিন। HR_POLICY.pdf পৃষ্ঠা ৩",
    )


def test_voice_configuration_for_supported_languages():
    rows = voice_rows()
    supported = [row for row in rows if row["language"] in LANGUAGES]

    assert len(supported) == 9

    for row in supported:
        assert row["stt_supported"] is True
        assert row["tts_supported"] is True
        assert row["stt_language_code"].endswith("-IN")
        assert row["tts_language_code"].endswith("-IN")
        assert row["tts_voice"]
        assert row["sample_transcript_matches_language"] is True

        if row["language"] == "en":
            assert row["stt_format"] == "transcribe"
            assert row["tts_voice"] == "Pranav"
        elif row["language"] == "ta":
            assert row["stt_format"] == "verbatim"
            assert row["tts_voice"] == "Nalini"
        else:
            assert row["stt_format"] == "verbatim"

    unsupported = {row["language"]: row for row in rows if row["language"] in {"or", "ur"}}
    assert unsupported["or"]["stt_supported"] is False
    assert unsupported["ur"]["tts_supported"] is False


def test_retrieval_against_policy_index():
    rows = evaluate_retrieval()
    voice = voice_rows()
    write_report(rows, voice)

    misses = [
        f"{row['language']}:{row['topic']}"
        for row in rows
        if not row["retrieval_returned_correct_source"]
    ]

    assert not misses, "Retrieval missed: " + ", ".join(misses)

    english_paternity = next(
        row
        for row in rows
        if row["language"] == "en" and row["topic"] == "paternity_leave"
    )
    assert english_paternity["retrieved_sources"]
    assert any(
        str(item["source"]).endswith("HR_POLICY.pdf") and int(item["page"]) == 4
        for item in english_paternity["retrieved_sources"]
    )


def test_preserved_project_voices_match_gnani_codes():
    assert build_stt_request_options("en")["language_code"] == "en-IN"
    assert build_stt_request_options("ta")["language_code"] == "ta-IN"
    assert resolve_tts_voice("en")["voice"] == "Pranav"
    assert resolve_tts_voice("ta")["voice"] == "Nalini"


if __name__ == "__main__":
    checks = [
        test_dataset_covers_every_interface_language_and_topic,
        test_answer_scoring_examples,
        test_voice_configuration_for_supported_languages,
        test_preserved_project_voices_match_gnani_codes,
        test_retrieval_against_policy_index,
    ]

    for check in checks:
        print(f"Running {check.__name__}...")
        check()
        print("  passed")

    print("Multilingual evaluation passed.")
