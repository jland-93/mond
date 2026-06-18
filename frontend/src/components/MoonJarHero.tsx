/**
 * 🏺 MoonJarHero — 달항아리 실루엣
 *
 * 조선 백자 moon jar의 좌우 비대칭(0.97/1.03)을 그대로 SVG로.
 * Login/MFA의 hero에 사용. 진입 시 1.2s 동안 아래에서 위로 차오르는 애니메이션
 * — 달이 떠오르듯, 신뢰가 차오르듯.
 */

import { useEffect, useState } from "react";

export interface MoonJarHeroProps {
  size?: number;
  /** 0..1 — 진행도. 비우면 자동으로 1까지 차오름. */
  fill?: number;
  className?: string;
}

export default function MoonJarHero({ size = 240, fill, className }: MoonJarHeroProps) {
  const [progress, setProgress] = useState(fill ?? 0);

  useEffect(() => {
    if (fill !== undefined) {
      setProgress(fill);
      return;
    }
    // 진입 애니메이션 — 0 → 1 (1200ms ease-moonrise)
    const reduceMotion =
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setProgress(1);
      return;
    }
    const start = performance.now();
    const duration = 1200;
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // ease-moonrise: cubic-bezier(0.22, 0.61, 0.36, 1)
      const eased = 1 - Math.pow(1 - t, 3);
      setProgress(eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [fill]);

  // 항아리 path — 좌우 의도된 비대칭 (좌 60→50 곡선 vs 우 140→152 곡선)
  const jarPath = `
    M 60 60
    C 40 78, 35 130, 50 172
    C 60 202, 84 214, 100 214
    C 118 214, 145 200, 152 170
    C 168 130, 162 78, 140 60
    C 130 50, 115 48, 100 48
    C 86 48, 72 50, 60 60 Z
  `;

  return (
    <svg
      width={size}
      height={(size * 240) / 200}
      viewBox="0 0 200 240"
      className={className}
      role="img"
      aria-label="달항아리 — Mond"
    >
      <defs>
        <radialGradient id="moon-jar-grad" cx="0.42" cy="0.4" r="0.7">
          <stop offset="0%" stopColor="oklch(94% 0.04 180)" />
          <stop offset="55%" stopColor="oklch(78% 0.06 180)" />
          <stop offset="100%" stopColor="oklch(50% 0.04 200)" />
        </radialGradient>
        {/* 매우 미세한 noise (banding 방지, 손맛) */}
        <filter id="jar-noise" x="0" y="0" width="100%" height="100%">
          <feTurbulence baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
          <feComponentTransfer>
            <feFuncA type="linear" slope="0.05" />
          </feComponentTransfer>
          <feComposite in2="SourceGraphic" operator="in" />
        </filter>
        {/* 차오르는 mask — 아래에서 위로 */}
        <clipPath id="jar-fill">
          <rect
            x="0"
            y={240 * (1 - progress)}
            width="200"
            height={240 * progress}
          />
        </clipPath>
      </defs>

      {/* 항아리 본체 — gradient + clip-path로 차오름 */}
      <path d={jarPath} fill="url(#moon-jar-grad)" clipPath="url(#jar-fill)" />

      {/* outline — 항상 보임 */}
      <path
        d={jarPath}
        fill="none"
        stroke="oklch(72% 0.05 180 / 0.5)"
        strokeWidth="0.7"
      />

      {/* 살짝의 하이라이트 — 좌상단 글로우 */}
      <ellipse
        cx="78"
        cy="92"
        rx="22"
        ry="14"
        fill="oklch(96% 0.05 180 / 0.18)"
        clipPath="url(#jar-fill)"
      />

      {/* 미세 noise overlay */}
      <path d={jarPath} fill="oklch(50% 0 0 / 0.06)" filter="url(#jar-noise)" />
    </svg>
  );
}
