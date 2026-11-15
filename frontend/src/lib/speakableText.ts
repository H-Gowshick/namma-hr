/**
 * Prepare assistant answers for Gnani TTS.
 * Markdown, citations, and long policy dumps make synthesis slow.
 */

const MAX_SPEAK_CHARS = 900;

export function toSpeakableText(raw: string): string {
  let text = (raw || "").replace(/\r\n/g, "\n");

  // Drop fenced code blocks and tables first.
  text = text.replace(/```[\s\S]*?```/g, " ");
  text = text.replace(/^\s*\|.*$/gm, " ");
  text = text.replace(/^\s*[-*_]{3,}\s*$/gm, " ");

  // Strip common markdown markers.
  text = text
    .replace(/!\[[^\]]*]\([^)]*\)/g, " ")
    .replace(/\[([^\]]+)]\([^)]*\)/g, "$1")
    .replace(/[*_~`>#]+/g, " ")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "");

  // Citations and source footnotes are for reading, not speaking.
  text = text.replace(/HR_POLICY\.pdf[^\n.]{0,60}/gi, " ");
  text = text.replace(
    /\((?:source|sources|citation|citations)[^)]*\)/gi,
    " ",
  );
  text = text.replace(
    /(?:source|sources)\s*[:：]\s*[^\n]+/gi,
    " ",
  );

  text = text.replace(/\s+/g, " ").trim();

  if (text.length <= MAX_SPEAK_CHARS) {
    return text;
  }

  const clipped = text.slice(0, MAX_SPEAK_CHARS);
  const sentenceEnd = Math.max(
    clipped.lastIndexOf(". "),
    clipped.lastIndexOf("? "),
    clipped.lastIndexOf("! "),
    clipped.lastIndexOf("। "),
  );

  if (sentenceEnd >= Math.floor(MAX_SPEAK_CHARS * 0.55)) {
    return clipped.slice(0, sentenceEnd + 1).trim();
  }

  const wordEnd = clipped.lastIndexOf(" ");
  return (wordEnd > 0 ? clipped.slice(0, wordEnd) : clipped).trim();
}
