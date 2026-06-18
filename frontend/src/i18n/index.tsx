/**
 * Mond — 자체 i18n Provider
 *
 * react-i18next 같은 외부 의존성 없이 가벼운 사전 기반.
 * 한국어 기본 + 영어 토글, localStorage에 선택 지속.
 */

import koKR from "antd/locale/ko_KR";
import enUS from "antd/locale/en_US";
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import { en } from "./en";
import { ko, type Dict } from "./ko";

export type Locale = "ko" | "en";

const STORAGE_KEY = "mond.locale";
const DEFAULT: Locale =
  ((globalThis as { __MOND_DEFAULT_LOCALE__?: string }).__MOND_DEFAULT_LOCALE__ as Locale) ?? "ko";

const DICTS: Record<Locale, Dict> = { ko, en };
const ANTD_LOCALES = { ko: koKR, en: enUS };

interface I18nValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: Dict;
  antdLocale: typeof koKR;
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const initial = (() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "ko" || saved === "en") return saved;
    } catch {
      /* ignore */
    }
    return DEFAULT;
  })();

  const [locale, setLocaleState] = useState<Locale>(initial);

  const value = useMemo<I18nValue>(
    () => ({
      locale,
      setLocale: (l) => {
        setLocaleState(l);
        try {
          localStorage.setItem(STORAGE_KEY, l);
        } catch {
          /* ignore */
        }
      },
      t: DICTS[locale],
      antdLocale: ANTD_LOCALES[locale],
    }),
    [locale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
