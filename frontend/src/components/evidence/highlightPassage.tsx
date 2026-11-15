import type { ReactNode } from "react";

const STOPWORDS = new Set([
  "a",
  "an",
  "the",
  "is",
  "are",
  "was",
  "were",
  "what",
  "how",
  "many",
  "much",
  "can",
  "could",
  "does",
  "do",
  "of",
  "for",
  "to",
  "in",
  "on",
  "be",
  "with",
  "and",
  "or",
  "under",
  "this",
  "that",
  "it",
  "company",
  "policy",
  "leave",
  "employee",
]);

function collectHighlightTerms(sources: string[]): string[] {
  const terms = new Set<string>();

  for (const source of sources) {
    const words = source.toLowerCase().match(/[a-zA-Z]{4,}/g) ?? [];
    for (const word of words) {
      if (!STOPWORDS.has(word)) {
        terms.add(word);
      }
    }

    const phrases =
      source.toLowerCase().match(
        /\b(?:casual|sick|medical|earned|privilege|privileged|maternity|paternity|work from home|carry forward)\s+leave\b|\bwork from home\b/g,
      ) ?? [];

    for (const phrase of phrases) {
      terms.add(phrase.trim());
    }
  }

  return [...terms].sort((a, b) => b.length - a.length);
}

/**
 * Highlight retrieval-query terms inside a real policy passage.
 * Never highlights LLM answer text as if it were a PDF quotation.
 */
export function highlightPassage(
  text: string,
  highlightSources: string[],
): ReactNode {
  const terms = collectHighlightTerms(highlightSources);

  if (!text || terms.length === 0) {
    return text;
  }

  const escaped = terms.map((term) =>
    term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
  );
  const pattern = new RegExp(`(${escaped.join("|")})`, "gi");
  const parts = text.split(pattern);

  return parts.map((part, index) => {
    const isMatch = terms.some(
      (term) => part.toLowerCase() === term.toLowerCase(),
    );

    if (!isMatch) {
      return <span key={`p-${index}`}>{part}</span>;
    }

    return (
      <mark key={`m-${index}`} className="evidence-mark">
        {part}
      </mark>
    );
  });
}
