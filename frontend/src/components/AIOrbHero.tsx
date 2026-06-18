/**
 * 🌐 AIOrbHero — AI 정체성을 보여주는 추상 sphere
 *
 * 달항아리(한국 정체성 강함) 대신 더 글로벌·AI/Tech 톤의 추상 orb.
 * 옥색·보라 그라데이션 mesh + floating particles + 미세한 회전.
 * Anthropic Claude / Linear / Vercel의 hero 그래픽 톤.
 */

import { useEffect, useState } from "react";

export interface AIOrbHeroProps {
  size?: number;
  className?: string;
}

export default function AIOrbHero({ size = 320, className }: AIOrbHeroProps) {
  const [t, setT] = useState(0);

  useEffect(() => {
    const reduceMotion =
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      setT((now - start) / 1000);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  // 매우 느린 회전 + 미세 부유
  const slowRot = (t * 6) % 360;
  const float = Math.sin(t * 0.6) * 8;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 320 320"
      className={className}
      role="img"
      aria-label="Mond"
      style={{ overflow: "visible" }}
    >
      <defs>
        {/* 메인 그라데이션 — 옥색 → 보라 → 검정 */}
        <radialGradient id="orb-main" cx="0.38" cy="0.36" r="0.62">
          <stop offset="0%" stopColor="oklch(96% 0.04 180)" stopOpacity="1" />
          <stop offset="35%" stopColor="oklch(82% 0.08 180)" stopOpacity="0.95" />
          <stop offset="65%" stopColor="oklch(54% 0.12 250)" stopOpacity="0.85" />
          <stop offset="100%" stopColor="oklch(22% 0.04 270)" stopOpacity="0.65" />
        </radialGradient>

        {/* 외곽 glow */}
        <radialGradient id="orb-glow" cx="0.5" cy="0.5" r="0.55">
          <stop offset="40%" stopColor="oklch(82% 0.08 180 / 0.30)" />
          <stop offset="70%" stopColor="oklch(72% 0.10 250 / 0.18)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>

        {/* 하이라이트 — 좌상단 작은 광택 */}
        <radialGradient id="orb-spec" cx="0.32" cy="0.28" r="0.18">
          <stop offset="0%" stopColor="oklch(98% 0.02 180 / 0.85)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>

        {/* mesh 패턴 — Anthropic 톤의 부드러운 흐름 */}
        <radialGradient id="orb-mesh-a" cx="0.7" cy="0.65" r="0.4">
          <stop offset="0%" stopColor="oklch(72% 0.18 295 / 0.5)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
        <radialGradient id="orb-mesh-b" cx="0.25" cy="0.75" r="0.35">
          <stop offset="0%" stopColor="oklch(86% 0.10 170 / 0.6)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>

        {/* 미세 noise — banding 방지, 손맛 */}
        <filter id="orb-noise" x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence baseFrequency="1.1" numOctaves="2" stitchTiles="stitch" />
          <feComponentTransfer>
            <feFuncA type="linear" slope="0.08" />
          </feComponentTransfer>
          <feComposite in2="SourceGraphic" operator="in" />
        </filter>

        <filter id="orb-blur">
          <feGaussianBlur stdDeviation="20" />
        </filter>
      </defs>

      {/* 외곽 큰 글로우 (배경에서 외롭지 않게) */}
      <circle cx="160" cy={160 + float} r="180" fill="url(#orb-glow)" />

      {/* 메인 orb */}
      <g transform={`translate(0, ${float}) rotate(${slowRot} 160 160)`}>
        <circle cx="160" cy="160" r="92" fill="url(#orb-main)" />
        {/* mesh layers */}
        <circle cx="160" cy="160" r="92" fill="url(#orb-mesh-a)" style={{ mixBlendMode: "screen" }} />
        <circle cx="160" cy="160" r="92" fill="url(#orb-mesh-b)" style={{ mixBlendMode: "screen" }} />
      </g>

      {/* 좌상단 하이라이트 — 회전 안 함 */}
      <circle cx="160" cy={160 + float} r="92" fill="url(#orb-spec)" />

      {/* 미세 noise */}
      <circle cx="160" cy={160 + float} r="92" fill="oklch(50% 0 0 / 0.06)" filter="url(#orb-noise)" />

      {/* 떠다니는 입자 (subtle) — 5개, 느린 회전 */}
      {[0, 1, 2, 3, 4].map((i) => {
        const angle = (slowRot * 0.5 + i * 72) * (Math.PI / 180);
        const dist = 130 + Math.sin(t * 0.4 + i) * 6;
        const cx = 160 + Math.cos(angle) * dist;
        const cy = 160 + Math.sin(angle) * dist + float * 0.5;
        const r = 1.4 + (i % 2) * 0.6;
        return (
          <circle
            key={i}
            cx={cx}
            cy={cy}
            r={r}
            fill="oklch(94% 0.04 180)"
            opacity={0.5 - (i % 3) * 0.12}
          />
        );
      })}
    </svg>
  );
}
