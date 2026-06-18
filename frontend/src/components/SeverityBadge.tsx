/**
 * SeverityBadge — icon + label + color 3종 세트
 *
 * WCAG 2.2 AA color-blindness 친화. 색에만 의존하지 않는다.
 * 어디서나 동일한 시그니처로 severity를 표현하기 위해 단일 컴포넌트.
 *
 * 사용: <SeverityBadge severity="critical" /> 또는 <SeverityBadge severity={f.severity} />
 */

import {
  CloseCircleFilled,
  ExclamationCircleFilled,
  InfoCircleFilled,
  MinusCircleFilled,
  WarningFilled,
} from "@ant-design/icons";
import { Tag } from "antd";
import type { CSSProperties } from "react";

export type SeverityKey = "critical" | "high" | "medium" | "low" | "info" | string;

const META: Record<
  string,
  {
    label_ko: string;
    label_en: string;
    color: string;
    bg: string;
    icon: React.ReactNode;
    order: number;
  }
> = {
  critical: {
    label_ko: "치명",
    label_en: "Critical",
    color: "var(--severity-critical)",
    bg: "var(--severity-critical-bg)",
    icon: <CloseCircleFilled aria-label="Critical" />,
    order: 0,
  },
  high: {
    label_ko: "높음",
    label_en: "High",
    color: "var(--severity-high)",
    bg: "var(--severity-high-bg)",
    icon: <WarningFilled aria-label="High" />,
    order: 1,
  },
  medium: {
    label_ko: "중간",
    label_en: "Medium",
    color: "var(--severity-medium)",
    bg: "var(--severity-medium-bg)",
    icon: <ExclamationCircleFilled aria-label="Medium" />,
    order: 2,
  },
  low: {
    label_ko: "낮음",
    label_en: "Low",
    color: "var(--severity-low)",
    bg: "var(--severity-low-bg)",
    icon: <MinusCircleFilled aria-label="Low" />,
    order: 3,
  },
  info: {
    label_ko: "정보",
    label_en: "Info",
    color: "var(--severity-info)",
    bg: "var(--severity-info-bg)",
    icon: <InfoCircleFilled aria-label="Info" />,
    order: 4,
  },
};

const FALLBACK = {
  label_ko: "—",
  label_en: "—",
  color: "var(--mond-text-dim)",
  bg: "var(--mond-surface-2)",
  icon: <InfoCircleFilled aria-label="Unknown" />,
  order: 99,
};

export interface SeverityBadgeProps {
  severity: SeverityKey | null | undefined;
  locale?: "ko" | "en";
  /** 'tag' (기본, antd Tag) | 'plain' (icon+label만, 표 셀에 적합) */
  variant?: "tag" | "plain";
  /** 라벨 숨기기 (icon-only, 좁은 공간) */
  iconOnly?: boolean;
  style?: CSSProperties;
}

export default function SeverityBadge({
  severity,
  locale = "ko",
  variant = "tag",
  iconOnly = false,
  style,
}: SeverityBadgeProps) {
  const key = (severity || "").toLowerCase();
  const m = META[key] ?? FALLBACK;
  const label = locale === "ko" ? m.label_ko : m.label_en;

  if (variant === "plain") {
    return (
      <span
        role="img"
        aria-label={label}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          color: m.color,
          fontWeight: 500,
          ...style,
        }}
      >
        {m.icon}
        {!iconOnly && <span>{label}</span>}
      </span>
    );
  }

  return (
    <Tag
      style={{
        background: m.bg,
        color: m.color,
        border: `1px solid ${m.color}`,
        borderRadius: 6,
        fontWeight: 500,
        padding: "1px 8px",
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        margin: 0,
        ...style,
      }}
    >
      {m.icon}
      {!iconOnly && label}
    </Tag>
  );
}

/** 정렬용 — severity를 숫자 order로. */
export function severityOrder(s: SeverityKey | null | undefined): number {
  return META[(s || "").toLowerCase()]?.order ?? 99;
}
