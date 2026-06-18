/**
 * 🌒 MoonPhase — Mond의 시그니처 시각 언어
 *
 * severity / progress / 상태를 달 위상으로 통일된 메타포로 표현한다.
 * 좌우 비대칭(0.97/1.03)으로 달항아리의 불완전의 미를 유지 — AI 디폴트의
 * 완벽한 원과 즉시 구별된다.
 *
 *  phase: 0 = 그믐 (critical), 0.25 = 상현, 0.5 = 반달, 0.75 = 하현, 1 = 보름 (healthy)
 */

import type { CSSProperties } from "react";

export interface MoonPhaseProps {
  /** 0..1 — 0=new moon (critical), 1=full moon (healthy) */
  phase: number;
  size?: number;
  /** 달 본체 색. 미지정 시 currentColor */
  color?: string;
  /** 그림자(보이지 않는 부분)의 배경색. 미지정 시 surface-0 */
  shadowColor?: string;
  className?: string;
  style?: CSSProperties;
}

export default function MoonPhase({
  phase,
  size = 24,
  color = "currentColor",
  shadowColor = "var(--surface-0)",
  className,
  style,
}: MoonPhaseProps) {
  const p = Math.max(0, Math.min(1, phase));
  const r = size / 2;
  // 좌우 비대칭 — 달항아리의 불완전성
  const rx = r * 1.0;
  const ry = r * 0.97;

  // 그림자 ellipse를 본체 위에 얹어 위상 표현
  // phase 0   → 그림자가 전체를 덮음 (그믐)
  // phase 0.5 → 그림자가 절반 (반달)
  // phase 1   → 그림자 없음 (보름)
  const k = 1 - 2 * p; // -1..1 (음수일수록 우측 그림자, 양수일수록 좌측)
  const shadowRx = Math.abs(k) * rx;
  const shadowDx = k > 0 ? rx - shadowRx : -(rx - shadowRx);

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      style={style}
      aria-hidden
    >
      <ellipse cx={r} cy={r} rx={rx} ry={ry} fill={color} />
      {p < 1 && (
        <ellipse
          cx={r + shadowDx}
          cy={r}
          rx={shadowRx}
          ry={ry}
          fill={shadowColor}
        />
      )}
    </svg>
  );
}

/** severity → phase 매핑. 보안 카드 / 표 등에서 일관되게 사용. */
export function phaseForSeverity(severity: string | null | undefined): number {
  switch ((severity || "").toLowerCase()) {
    case "critical": return 0.04;   // 거의 그믐
    case "high":     return 0.25;
    case "medium":   return 0.5;
    case "low":      return 0.78;
    case "info":     return 0.9;
    case "healthy":  return 1;
    default:         return 0.5;
  }
}
