import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Normalmente se entra por nginx (http://localhost:8080). Este proxy permite usar Vite directamente si hace falta.
    proxy: { "/api": "http://backend:8000" },
    watch: { usePolling: true }, // Necesario para detectar cambios desde Windows dentro de Docker
  },
});
