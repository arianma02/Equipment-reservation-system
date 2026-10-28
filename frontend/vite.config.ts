import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  envDir: mode === "test" ? false : undefined,
  define:
    mode === "test"
      ? {
          "import.meta.env.VITE_API_URL": JSON.stringify(
            "http://127.0.0.1:8000",
          ),
        }
      : undefined,
  plugins: [react()],
}));
