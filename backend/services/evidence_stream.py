"""Serialize retrieved HR passages for the streaming chat envelope.

The frontend strips this envelope before rendering the answer so
LLM-generated citation prose is never treated as a PDF quotation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EVIDENCE_START = "<<<NAMMA_EVIDENCE>>>"
EVIDENCE_END = "<<<END_EVIDENCE>>>"


def _basename(source: Any) -> str:
    value = str(source or "").strip()
    if not value:
        return "Unknown source"
    return Path(value).name or value


def _page_value(page: Any) -> int | str:
    if page is None or page == "":
        return "Unknown page"

    try:
        return int(page)
    except (TypeError, ValueError):
        text = str(page).strip()
        return text or "Unknown page"


def serialize_evidence_items(results: list[dict]) -> list[dict]:
    """
    Map retrieve_multi rows into a stable client payload.

    Only fields that already exist on retrieval results are included.
    """

    items: list[dict] = []

    for index, item in enumerate(results, start=1):
        text = str(item.get("text") or "").strip()
        if not text:
            continue

        payload: dict[str, Any] = {
            "id": str(index),
            "source": _basename(item.get("source")),
            "page": _page_value(item.get("page")),
            "heading": str(item.get("heading") or "General").strip() or "General",
            "text": text,
        }

        matched_query = str(item.get("matched_query") or "").strip()
        if matched_query:
            payload["matched_query"] = matched_query

        relevance = item.get("relevance_score")
        if isinstance(relevance, (int, float)):
            payload["relevance_score"] = round(float(relevance), 4)

        items.append(payload)

    return items


def format_evidence_envelope(items: list[dict]) -> str:
    """Prefix streamed answers with structured retrieval evidence."""

    payload = {
        "version": 1,
        "items": items,
    }

    return (
        f"{EVIDENCE_START}"
        f"{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}"
        f"{EVIDENCE_END}"
    )
