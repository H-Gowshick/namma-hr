"""
Run the multilingual HR evaluation.

Retrieval is checked against the indexed HR_POLICY.pdf passages.
Answer language, facts, and citations are scored when --answers is set,
using the same chat service as the application.

Voice rows check the configured Gnani STT and TTS language codes.
They do not upload audio.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from evaluation.cases import (
    UNSUPPORTED_VOICE_LANGUAGES,
    VOICE_CASES,
    evaluation_cases,
)
from evaluation.score import score_case
from services.retrieval.pdf_retrieval import retrieve_multi
from services.hr_query_normalization import build_english_retrieval_queries
from services.stt_languages import (
    build_stt_request_options,
    is_voice_language_supported,
    transcript_matches_language,
)
from services.tts_voices import resolve_tts_voice

REPORT_PATH = Path(__file__).resolve().parent / "latest_report.json"


def retrieve_for_case(case: dict) -> list[dict]:
    queries = build_english_retrieval_queries(
        query=case["question"],
        language=case["language"],
        rewritten_query=None,
    )
    return retrieve_multi(queries, top_k=4)


def evaluate_retrieval() -> list[dict]:
    rows = []

    for case in evaluation_cases():
        results = retrieve_for_case(case)
        rows.append(score_case(case, results))

    return rows


def voice_rows() -> list[dict]:
    rows = []

    for case in VOICE_CASES:
        language = case["language"]
        stt = build_stt_request_options(language)
        tts = resolve_tts_voice(language)
        sample = case["spoken_question"]

        rows.append(
            {
                "language": language,
                "spoken_question": sample,
                "stt_supported": is_voice_language_supported(language),
                "stt_language_code": stt["language_code"],
                "stt_format": stt["format"],
                "sample_transcript_matches_language": transcript_matches_language(
                    sample,
                    language,
                ),
                "tts_supported": True,
                "tts_language_code": tts["language_code"],
                "tts_voice": tts["voice"],
            }
        )

    for language in UNSUPPORTED_VOICE_LANGUAGES:
        rows.append(
            {
                "language": language,
                "spoken_question": None,
                "stt_supported": is_voice_language_supported(language),
                "stt_language_code": None,
                "stt_format": None,
                "sample_transcript_matches_language": False,
                "tts_supported": False,
                "tts_language_code": None,
                "tts_voice": None,
                "note": "Not an interface language. Gnani does not list this language.",
            }
        )

    return rows


async def _answer_case(case: dict) -> str:
    from schemas.chat import chatMessage
    from services.chat import chat_service

    messages = [chatMessage(role="user", content=case["question"])]
    parts: list[str] = []

    async for chunk in chat_service(messages, language=case["language"]):
        parts.append(chunk)

    answer = "".join(parts).strip()

    if "the chat request failed" in answer.lower():
        raise RuntimeError(answer)

    return answer


async def evaluate_with_answers() -> list[dict]:
    rows = []
    cases = evaluation_cases()

    for index, case in enumerate(cases, start=1):
        print(
            f"Answering {index}/{len(cases)} {case['language']} {case['topic']}",
            flush=True,
        )
        results = retrieve_for_case(case)

        try:
            answer = await _answer_case(case)
        except Exception as exc:
            answer = f"Evaluation error: {exc}"

        rows.append(score_case(case, results, answer))

    return rows


def rescore_saved_answers() -> list[dict]:
    """
    Score answers already stored in latest_report.json.
    This does not call Groq again.
    """

    saved = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    by_key = {
        (case["language"], case["topic"]): case
        for case in evaluation_cases()
    }
    rows = []

    for saved_row in saved["cases"]:
        case = by_key[(saved_row["language"], saved_row["topic"])]
        results = [
            {"source": item.get("source"), "page": item.get("page"), "text": ""}
            for item in saved_row.get("retrieved_sources") or []
        ]
        # Retrieval was already scored. Keep that result, and rescore the answer.
        row = score_case(case, results, saved_row.get("answer"))
        row["retrieval_returned_correct_source"] = saved_row[
            "retrieval_returned_correct_source"
        ]
        row["retrieved_sources"] = saved_row.get("retrieved_sources") or []
        rows.append(row)

    return rows


def summarize(rows: list[dict]) -> dict:
    total = len(rows)
    retrieval_hits = sum(row["retrieval_returned_correct_source"] for row in rows)

    def counted(field: str) -> tuple[int, int]:
        scored = [row[field] for row in rows if row[field] is not None]
        return sum(bool(item) for item in scored), len(scored)

    language_hits, language_scored = counted("answer_used_requested_language")
    fact_hits, fact_scored = counted("answer_factually_correct")
    citation_hits, citation_scored = counted("citations_present_and_correct")

    return {
        "cases": total,
        "retrieval_correct": retrieval_hits,
        "answers_scored": language_scored,
        "answer_language_correct": language_hits,
        "answer_factually_correct": fact_hits,
        "citations_correct": citation_hits,
        "facts_scored": fact_scored,
        "citations_scored": citation_scored,
        "answers_failed": sum(bool(row.get("answer_error")) for row in rows),
    }


def write_report(rows: list[dict], voice: list[dict]) -> None:
    payload = {
        "source_pdf": "HR_POLICY.pdf",
        "summary": summarize(rows),
        "cases": rows,
        "voice": voice,
    }
    REPORT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Namma HR multilingual evaluation.")
    parser.add_argument(
        "--answers",
        action="store_true",
        help="Also call the chat model and score language, facts, and citations.",
    )
    parser.add_argument(
        "--rescore",
        action="store_true",
        help="Rescore answers already saved in latest_report.json. Does not call Groq.",
    )
    args = parser.parse_args()

    if args.answers and args.rescore:
        parser.error("Use only one of --answers or --rescore.")

    if args.rescore:
        rows = rescore_saved_answers()
    elif args.answers:
        rows = asyncio.run(evaluate_with_answers())
    else:
        rows = evaluate_retrieval()

    voice = voice_rows()
    write_report(rows, voice)
    summary = summarize(rows)

    print(
        "Cases: {cases}. Retrieval correct: {retrieval_correct}/{cases}.".format(
            **summary
        )
    )

    if summary["answers_scored"]:
        print(
            "Answer language: {answer_language_correct}/{answers_scored}. "
            "Facts: {answer_factually_correct}/{facts_scored}. "
            "Citations: {citations_correct}/{citations_scored}. "
            "Unscored because the model call failed: {answers_failed}.".format(**summary)
        )
    else:
        print("Answer scoring was not run. Use --answers to call the chat model.")

    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
