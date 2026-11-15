import type { ProxyOptions } from "vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function backendProxy(): ProxyOptions {
  return {
    target: "http://127.0.0.1:8000",
    changeOrigin: true,
    configure(proxy) {
      // Keep chat token streams chunked — default proxy buffering
      // makes the UI show the full answer in one jump.
      proxy.on("proxyRes", (proxyRes) => {
        proxyRes.headers["cache-control"] = "no-cache, no-transform";
        proxyRes.headers["x-accel-buffering"] = "no";
        delete proxyRes.headers["content-length"];
      });
    },
  };
}

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/chat": backendProxy(),
      "/structured-chat": backendProxy(),
      "/tool-chat": backendProxy(),
      "/documents": backendProxy(),
      "/retrieve": backendProxy(),
      "/voice": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
