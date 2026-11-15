import { apiUrl } from "./apiBase";
import type { EvidenceItem, EvidencePayload } from "./evidenceTypes";

export const EVIDENCE_START = "<<<NAMMA_EVIDENCE>>>";
export const EVIDENCE_END = "<<<END_EVIDENCE>>>";

export type ParsedEvidenceStream = {
  answer: string;
  evidence: EvidenceItem[] | null;
  evidenceReady: boolean;
};

function isEvidenceItem(value: unknown): value is EvidenceItem {
  if (!value || typeof value !== "object") {
    return false;
  }

  const item = value as Record<string, unknown>;

  return (
    typeof item.id === "string" &&
    typeof item.source === "string" &&
    (typeof item.page === "number" || typeof item.page === "string") &&
    typeof item.heading === "string" &&
    typeof item.text === "string"
  );
}

function parseEvidencePayload(raw: string): EvidenceItem[] {
  try {
    const parsed = JSON.parse(raw) as EvidencePayload;

    if (!parsed || !Array.isArray(parsed.items)) {
      return [];
    }

    return parsed.items.filter(isEvidenceItem).map((item) => ({
      id: item.id,
      source: item.source,
      page: item.page,
      heading: item.heading,
      text: item.text,
      ...(typeof item.matched_query === "string"
        ? { matched_query: item.matched_query }
        : {}),
      ...(typeof item.relevance_score === "number"
        ? { relevance_score: item.relevance_score }
        : {}),
    }));
  } catch {
    return [];
  }
}

/**
 * Split a streamed /chat body into structured evidence + answer text.
 * Evidence is only taken from the backend envelope, never from LLM prose.
 */
export function parseEvidenceStream(raw: string): ParsedEvidenceStream {
  const start = raw.indexOf(EVIDENCE_START);

  if (start === -1) {
    return {
      answer: raw,
      evidence: null,
      evidenceReady: false,
    };
  }

  const jsonStart = start + EVIDENCE_START.length;
  const end = raw.indexOf(EVIDENCE_END, jsonStart);

  if (end === -1) {
    return {
      answer: "",
      evidence: null,
      evidenceReady: false,
    };
  }

  const jsonText = raw.slice(jsonStart, end);
  const answer = raw.slice(end + EVIDENCE_END.length);

  return {
    answer,
    evidence: parseEvidencePayload(jsonText),
    evidenceReady: true,
  };
}

export function documentPageUrl(
  source: string,
  page: number | string,
): string | null {
  const filename = source.trim().split(/[\\/]/).pop() ?? "";

  if (!filename.toLowerCase().endsWith(".pdf")) {
    return null;
  }

  const pageNumber =
    typeof page === "number"
      ? page
      : Number.parseInt(String(page).replace(/[^\d]/g, ""), 10);

  const hash =
    Number.isFinite(pageNumber) && pageNumber > 0 ? `#page=${pageNumber}` : "";

  return apiUrl(`/documents/${encodeURIComponent(filename)}${hash}`);
}
