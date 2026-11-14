import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: { manualChunks: { charts: ["recharts"], graph: ["cytoscape"] } },
    },
  },
  server: {
    proxy: Object.fromEntries(
      ["/api", "/docs", "/openapi.json"].map((path) => [
        path,
        { target: "http://127.0.0.1:8000", changeOrigin: true },
      ]),
    ),
  },
});
