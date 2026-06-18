/**
 * ✨ AiGeneratedChip — AI 자동 생성/분석 결과 시그니처
 *
 * Cursor의 "Agent Window 분리" + YouTube의 AI 콘텐츠 명시 + 1Password의
 * 데이터 처리 투명성을 통합. 사용자 입력 콘텐츠와 시각적으로 분리한다.
 */

import { Tooltip } from "antd";
import MoonPhase from "./MoonPhase";

export interface AiGeneratedChipProps {
  model?: string;
  tooltip?: string;
  size?: "sm" | "md";
}

export default function AiGeneratedChip({ model, tooltip, size = "sm" }: AiGeneratedChipProps) {
  const fontSize = size === "sm" ? 11 : 12;
  const moonSize = size === "sm" ? 11 : 14;
  const padding = size === "sm" ? "1px 8px 1px 6px" : "2px 10px 2px 8px";

  const label = (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding,
        border: "1px solid var(--accent-dim)",
        borderRadius: 999,
        fontSize,
        color: "var(--accent)",
        background: "color-mix(in oklch, var(--accent) 8%, transparent)",
        fontVariantNumeric: "tabular-nums",
        lineHeight: 1.4,
        userSelect: "none",
        whiteSpace: "nowrap",
      }}
    >
      <MoonPhase phase={0.78} size={moonSize} color="var(--accent)" shadowColor="transparent" />
      <span>AI</span>
      {model && (
        <span style={{ color: "var(--fg-tertiary)", fontFamily: "var(--font-mono)", fontSize: fontSize - 1 }}>
          · {model}
        </span>
      )}
    </span>
  );

  if (tooltip) return <Tooltip title={tooltip}>{label}</Tooltip>;
  return label;
}
