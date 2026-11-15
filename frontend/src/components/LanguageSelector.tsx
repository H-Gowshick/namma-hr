import type { ChangeEvent } from "react";

import {
  APP_LANGUAGES,
  isAppLanguageCode,
  languageOptionLabel,
} from "../lib/languages";
import type { AppLanguageCode } from "../lib/languages";

type LanguageSelectorProps = {
  value: AppLanguageCode;
  onChange: (language: AppLanguageCode) => void;
  id?: string;
};

export default function LanguageSelector({
  value,
  onChange,
  id = "language-selector",
}: LanguageSelectorProps) {
  const selected =
    APP_LANGUAGES.find((language) => language.code === value) ??
    APP_LANGUAGES[0];

  function handleChange(event: ChangeEvent<HTMLSelectElement>) {
    const nextLanguage = event.target.value;

    if (isAppLanguageCode(nextLanguage)) {
      onChange(nextLanguage);
    }
  }

  return (
    <div className="language-selector">
      <label className="language-selector-label" htmlFor={id}>
        Language
      </label>

      <span className="language-selector-control">
        <select
          id={id}
          value={value}
          onChange={handleChange}
          lang={selected.locale}
          title={languageOptionLabel(selected)}
        >
          {APP_LANGUAGES.map((language) => (
            <option
              key={language.code}
              value={language.code}
              lang={language.locale}
            >
              {languageOptionLabel(language)}
            </option>
          ))}
        </select>
      </span>
    </div>
  );
}
