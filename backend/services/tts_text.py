"""Prepare policy answers for faster Gnani Timbre synthesis."""

from __future__ import annotations

import re

MAX_SPEAK_CHARS = 900

_CODE_FENCE = re.compile(r"```[\s\S]*?```")
_TABLE_ROW = re.compile(r"^\s*\|.*$", re.MULTILINE)
_HORIZONTAL_RULE = re.compile(r"^\s*[-*_]{3,}\s*$", re.MULTILINE)
_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*]\([^)]*\)")
_MARKDOWN_MARKERS = re.compile(r"[*_~`>#]+")
_LIST_PREFIX = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+", re.MULTILINE)
_SOURCE_FILE = re.compile(r"HR_POLICY\.pdf[^\n.]{0,60}", re.IGNORECASE)
_SOURCE_PAREN = re.compile(
    r"\((?:source|sources|citation|citations)[^)]*\)",
    re.IGNORECASE,
)
_SOURCE_LINE = re.compile(
    r"(?:source|sources)\s*[:：]\s*[^\n]+",
    re.IGNORECASE,
)
_WHITESPACE = re.compile(r"\s+")


def to_speakable_text(raw: str, max_chars: int = MAX_SPEAK_CHARS) -> str:
    text = (raw or "").replace("\r\n", "\n")
    text = _CODE_FENCE.sub(" ", text)
    text = _TABLE_ROW.sub(" ", text)
    text = _HORIZONTAL_RULE.sub(" ", text)
    text = _MARKDOWN_LINK.sub(" ", text)
    text = _MARKDOWN_MARKERS.sub(" ", text)
    text = _LIST_PREFIX.sub("", text)
    text = _SOURCE_FILE.sub(" ", text)
    text = _SOURCE_PAREN.sub(" ", text)
    text = _SOURCE_LINE.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()

    if len(text) <= max_chars:
        return text

    clipped = text[:max_chars]
    sentence_end = max(
        clipped.rfind(". "),
        clipped.rfind("? "),
        clipped.rfind("! "),
        clipped.rfind("। "),
    )

    if sentence_end >= int(max_chars * 0.55):
        return clipped[: sentence_end + 1].strip()

    word_end = clipped.rfind(" ")
    return (clipped[:word_end] if word_end > 0 else clipped).strip()
