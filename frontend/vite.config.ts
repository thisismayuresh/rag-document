import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendOrigin = process.env.VITE_BACKEND_ORIGIN ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/health": backendOrigin,
      "/sessions": backendOrigin,
      "/documents": backendOrigin,
      "/chat": backendOrigin,
    },
  },
});
