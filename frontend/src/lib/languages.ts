// Session language choices for the chat UI.
// English is the default. The selected code is sent with
// each /chat request so answers follow that language.
//
// STT support: Gnani Prisma docs
// https://docs.gnani.ai/api/STT/languages
// TTS support: Gnani Timbre v2.5 docs
// https://docs.gnani.ai/api/TTS/available-voices
// Odia and Urdu are not offered. Gnani Prisma and Timbre do not list them.

export const APP_LANGUAGES = [
  {
    code: "en",
    locale: "en",
    englishName: "English",
    nativeName: "English",
    gnaniSttCode: "en-IN",
    gnaniTtsCode: "en-IN",
    ttsVoice: "Pranav",
    voiceSupported: true,
    ttsSupported: true,
  },
  {
    code: "hi",
    locale: "hi",
    englishName: "Hindi",
    nativeName: "हिन्दी",
    gnaniSttCode: "hi-IN",
    gnaniTtsCode: "hi-IN",
    ttsVoice: "Deepak",
    voiceSupported: true,
    ttsSupported: true,
  },
  {
    code: "ta",
    locale: "ta",
    englishName: "Tamil",
    nativeName: "தமிழ்",
    gnaniSttCode: "ta-IN",
    gnaniTtsCode: "ta-IN",
    ttsVoice: "Nalini",
    voiceSupported: true,
    ttsSupported: true,
  },
  {
    code: "te",
    locale: "te",
    englishName: "Telugu",
    nativeName: "తెలుగు",
    gnaniSttCode: "te-IN",
    gnaniTtsCode: "te-IN",
    ttsVoice: "Suhana",
    voiceSupported: true,
    ttsSupported: true,
  },
  {
    code: "kn",
    locale: "kn",
    englishName: "Kannada",
    nativeName: "ಕನ್ನಡ",
    gnaniSttCode: "kn-IN",
    gnaniTtsCode: "kn-IN",
    ttsVoice: "Saanvi",
    voiceSupported: true,
    ttsSupported: true,
  },
  {
    code: "ml",
    locale: "ml",
    englishName: "Malayalam",
    nativeName: "മലയാളം",
    gnaniSttCode: "ml-IN",
    gnaniTtsCode: "ml-IN",
    ttsVoice: "Reshma",
    voiceSupported: true,
    ttsSupported: true,
  },
  {
    code: "bn",
    locale: "bn",
    englishName: "Bengali",
    nativeName: "বাংলা",
    gnaniSttCode: "bn-IN",
    gnaniTtsCode: "bn-IN",
    ttsVoice: "Kirra",
    voiceSupported: true,
    ttsSupported: true,
  },
  {
    code: "mr",
    locale: "mr",
    englishName: "Marathi",
    nativeName: "मराठी",
    gnaniSttCode: "mr-IN",
    gnaniTtsCode: "mr-IN",
    ttsVoice: "Zahira",
    voiceSupported: true,
    ttsSupported: true,
  },
  {
    code: "gu",
    locale: "gu",
    englishName: "Gujarati",
    nativeName: "ગુજરાતી",
    gnaniSttCode: "gu-IN",
    gnaniTtsCode: "gu-IN",
    ttsVoice: "Falak",
    voiceSupported: true,
    ttsSupported: true,
  },
] as const;

export type AppLanguage = (typeof APP_LANGUAGES)[number];

export type AppLanguageCode = AppLanguage["code"];

export const DEFAULT_LANGUAGE: AppLanguageCode = "en";

export function isAppLanguageCode(value: string): value is AppLanguageCode {
  return APP_LANGUAGES.some((language) => language.code === value);
}

export function getAppLanguage(code: AppLanguageCode): AppLanguage {
  return (
    APP_LANGUAGES.find((language) => language.code === code) ?? APP_LANGUAGES[0]
  );
}

export function isVoiceLanguageSupported(code: AppLanguageCode): boolean {
  return getAppLanguage(code).voiceSupported;
}

export function isTtsLanguageSupported(code: AppLanguageCode): boolean {
  return getAppLanguage(code).ttsSupported;
}

export function unsupportedVoiceLanguageMessage(code: AppLanguageCode): string {
  const language = getAppLanguage(code);
  const supported = APP_LANGUAGES.filter((item) => item.voiceSupported)
    .map((item) => item.englishName)
    .join(", ");

  return (
    `Voice input is not available for ${language.englishName} yet. ` +
    `Supported voice languages: ${supported}. ` +
    "Please choose a supported language or type your question."
  );
}

export function unsupportedTtsLanguageMessage(code: AppLanguageCode): string {
  const language = getAppLanguage(code);
  const supported = APP_LANGUAGES.filter((item) => item.ttsSupported)
    .map((item) => item.englishName)
    .join(", ");

  return (
    `Voice output is not available for ${language.englishName} yet. ` +
    `Supported spoken languages: ${supported}. ` +
    "You can still read the text answer."
  );
}

export function languageOptionLabel(language: AppLanguage): string {
  if (language.nativeName === language.englishName) {
    return language.englishName;
  }

  return `${language.nativeName} · ${language.englishName}`;
}
