import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

// Flat config (ESLint 9+/10). Vite + React 19 + TypeScript 프로파일.
export default tseslint.config(
  { ignores: ["dist", "node_modules", "*.tsbuildinfo"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // rules-of-hooks 등 핵심은 error 유지. 아래 신규 aggressive 규칙은
      // URL 동기화·디바운스·비동기 기본값 등 정당한 effect 패턴을 넓게 잡으므로
      // 강제 차단 대신 advisory(warn) — 신규 코드에 가시화하되 기존 동작은 안 건드림.
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/immutability": "warn",
      "react-hooks/exhaustive-deps": "warn",
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
    },
  },
);
