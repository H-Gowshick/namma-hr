import { API_BASE_URL, apiWebSocketUrl } from "./apiBase";

/** Empty during local development so the Vite proxy receives voice requests. */
export const VOICE_HTTP_BASE = API_BASE_URL;

export function voiceWebSocketUrl(language: string): string {
  const params = new URLSearchParams({ language });
  return `${apiWebSocketUrl("/voice/transcribe-stream")}?${params}`;
}
