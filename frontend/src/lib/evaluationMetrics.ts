import snapshot from "../data/evaluationSnapshot.json" with { type: "json" };

export type EvalCase = {
  language: string;
  languageName: string;
  topic: string;
  title: string;
  retrievalCorrect: boolean;
  answerCorrect: boolean | null;
  citationCorrect: boolean | null;
  answerLanguageCorrect: boolean | null;
  answerError: string | null;
};

export type VoiceRow = {
  language: string;
  sttConfigured: boolean;
  sttLanguageCode: string | null;
  ttsConfigured: boolean;
  ttsLanguageCode: string | null;
  ttsVoice: string | null;
  sampleScriptMatched: boolean;
  note?: string;
};

export type OverallStatus =
  | "pass"
  | "fact-failed"
  | "call-failed"
  | "answer-not-evaluated";

const INTERFACE_LANGUAGES = [
  "en",
  "hi",
  "ta",
  "te",
  "kn",
  "ml",
  "bn",
  "mr",
  "gu",
] as const;

/**
 * Spoken playback the project recorded as already checked.
 * Source: backend/services/tts_voices.py. This is not in the scored JSON.
 */
const TTS_AUDIO_VERIFIED = new Set(["en", "ta"]);

export const evaluationSnapshot = snapshot;
export const evaluationCases = snapshot.cases as EvalCase[];
export const voiceRows = snapshot.voice as VoiceRow[];

export function ratioLabel(numerator: number, denominator: number): string {
  if (denominator <= 0) {
    return "Not evaluated";
  }

  return `${numerator}/${denominator}`;
}

export function overallStatus(row: EvalCase): OverallStatus {
  if (row.answerError) {
    return "call-failed";
  }

  if (row.answerCorrect === false) {
    return "fact-failed";
  }

  if (row.answerCorrect === null || row.citationCorrect === null) {
    return "answer-not-evaluated";
  }

  if (row.retrievalCorrect && row.answerCorrect && row.citationCorrect) {
    return "pass";
  }

  return "fact-failed";
}

export function overallLabel(status: OverallStatus): string {
  switch (status) {
    case "pass":
      return "Pass";
    case "fact-failed":
      return "Fact check failed";
    case "call-failed":
      return "Model call failed";
    case "answer-not-evaluated":
      return "Answer not evaluated";
  }
}

export type LanguageCoverage = {
  code: string;
  name: string;
  uiAvailable: boolean;
  textAnswersScored: number;
  textAnswersUnscored: number;
  retrievalTested: number;
  retrievalCorrect: number;
  sttConfigured: boolean;
  ttsConfigured: boolean;
  sttAudioVerified: false;
  ttsAudioVerified: boolean;
};

export function languageCoverage(): LanguageCoverage[] {
  return INTERFACE_LANGUAGES.map((code) => {
    const rows = evaluationCases.filter((item) => item.language === code);
    const voice = voiceRows.find((item) => item.language === code);
    const scored = rows.filter((item) => item.answerCorrect !== null);

    return {
      code,
      name: rows[0]?.languageName ?? code,
      uiAvailable: true,
      textAnswersScored: scored.length,
      textAnswersUnscored: rows.length - scored.length,
      retrievalTested: rows.length,
      retrievalCorrect: rows.filter((item) => item.retrievalCorrect).length,
      sttConfigured: Boolean(voice?.sttConfigured),
      ttsConfigured: Boolean(voice?.ttsConfigured),
      sttAudioVerified: false,
      ttsAudioVerified: TTS_AUDIO_VERIFIED.has(code),
    };
  });
}

export function failedCases(): EvalCase[] {
  return evaluationCases.filter((row) => {
    const status = overallStatus(row);
    return status === "fact-failed" || status === "call-failed";
  });
}

export const unavailableRagMetrics = [
  "Retrieval precision",
  "Retrieval recall",
  "Context relevance",
] as const;
