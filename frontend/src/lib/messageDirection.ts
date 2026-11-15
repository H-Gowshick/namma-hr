const URDU_LETTER = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/gu;
const LETTER = /\p{L}/gu;

export type MessageDirection = "ltr" | "rtl";

// Urdu uses the Arabic script and is the only right-to-left
// language this chat needs to isolate. A few Urdu words inside
// an English or Indic answer stay in the normal left-to-right bubble.
export function messageTextDirection(text: string): MessageDirection {
  const urduLetters = text.match(URDU_LETTER)?.length ?? 0;

  if (urduLetters === 0) {
    return "ltr";
  }

  const letters = text.match(LETTER)?.length ?? 0;

  if (letters > 0 && urduLetters / letters >= 0.35) {
    return "rtl";
  }

  return "ltr";
}
