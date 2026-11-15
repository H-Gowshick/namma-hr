/**
 * Groq answers often include narrow no-break spaces and other
 * Unicode separators that break word wrapping in the chat UI
 * (e.g. "m of 3 Casual Leave day" mid-line artifacts).
 */
const EXOTIC_SPACES = /[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000\uFEFF]/g;
const ZERO_WIDTH = /[\u200B-\u200D\u2060]/g;

export function normalizeMessageText(raw: string): string {
  return (raw || "")
    .replace(EXOTIC_SPACES, " ")
    .replace(ZERO_WIDTH, "")
    .replace(/\u2011/g, "-")
    .replace(/【\s*/g, "(")
    .replace(/\s*】/g, ")");
}
