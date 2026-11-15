import type { EvidenceItem } from "./evidenceTypes";
import type { AppLanguageCode } from "./languages";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  language: AppLanguageCode;
  evidence?: EvidenceItem[];
  evidenceReady?: boolean;
};

export type ChatApiMessage = {
  role: "user" | "assistant";
  content: string;
};
