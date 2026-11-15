/** Public API origin. Empty in local development so the Vite proxy is used. */

const configured = import.meta.env.VITE_API_BASE_URL ?? "";

export const API_BASE_URL = configured.trim().replace(/\/$/, "");

export function apiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
}

export function apiWebSocketUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;

  if (!API_BASE_URL) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}${normalized}`;
  }

  const base = new URL(API_BASE_URL);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = normalized;
  base.search = "";
  base.hash = "";
  return base.toString();
}
