import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Konfigurasi Vite untuk dashboard KALTIDE Intelligence
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
  },
});
