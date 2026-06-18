/**
 * CrescentMoonHero — 초승달이 우방향으로 천천히 회전하는 동적 hero
 *
 * 큰 disk(달 본체) 위에 offset된 shadow disk를 얹어 초승달 silhouette을 만들고,
 * 전체를 60s 한 바퀴 속도로 시계방향 회전. 떠다니는 별 + 외곽 글로우.
 */

export interface CrescentMoonHeroProps {
  size?: number;
  className?: string;
}

export default function CrescentMoonHero({ size = 240, className }: CrescentMoonHeroProps) {
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
        {/* 큰 disk — 옥색·청 그라데이션 (우측이 빛남) */}
        <radialGradient id="cres-grad" cx="0.72" cy="0.38" r="0.65">
          <stop offset="0%" stopColor="oklch(98% 0.04 180)" />
          <stop offset="35%" stopColor="oklch(86% 0.08 180)" />
          <stop offset="70%" stopColor="oklch(60% 0.10 230)" />
          <stop offset="100%" stopColor="oklch(34% 0.06 260)" />
        </radialGradient>

        {/* 외곽 ambient glow — 외롭지 않게 풍부한 배경 */}
        <radialGradient id="cres-ambient" cx="0.5" cy="0.5" r="0.55">
          <stop offset="45%" stopColor="oklch(82% 0.08 180 / 0.35)" />
          <stop offset="75%" stopColor="oklch(60% 0.10 250 / 0.18)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>

        {/* 작은 specular highlight */}
        <radialGradient id="cres-spec" cx="0.78" cy="0.32" r="0.13">
          <stop offset="0%" stopColor="oklch(99% 0.02 180 / 0.95)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>

        {/* 미세 noise — banding 방지, 손맛 */}
        <filter id="cres-noise" x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence baseFrequency="1.1" numOctaves="2" stitchTiles="stitch" />
          <feComponentTransfer>
            <feFuncA type="linear" slope="0.07" />
          </feComponentTransfer>
          <feComposite in2="SourceGraphic" operator="in" />
        </filter>

        {/* mask — 큰 원에서 좌측 작은 원을 빼서 초승달 모양 */}
        <mask id="crescent-shape">
          <rect x="-50" y="-50" width="420" height="420" fill="white" />
          {/* 좌측 약간 위로 offset된 shadow circle — 큰 원의 좌측을 가림 */}
          <circle cx="124" cy="148" r="92" fill="black" />
        </mask>
      </defs>

      {/* 외곽 ambient glow — 회전 안 함 */}
      <circle cx="160" cy="160" r="200" fill="url(#cres-ambient)" />

      {/* ── 회전하는 초승달 본체 + 별들 ─────────────────────────── */}
      <g className="mond-crescent-spin" style={{ transformOrigin: "160px 160px" }}>
        {/* 큰 disk → mask로 초승달 silhouette */}
        <circle cx="160" cy="160" r="100" fill="url(#cres-grad)" mask="url(#crescent-shape)" />

        {/* 우측 specular highlight */}
        <circle cx="160" cy="160" r="100" fill="url(#cres-spec)" mask="url(#crescent-shape)" />

        {/* 미세 noise */}
        <circle cx="160" cy="160" r="100" fill="oklch(50% 0 0 / 0.06)"
                mask="url(#crescent-shape)" filter="url(#cres-noise)" />

        {/* 외곽 hairline — 초승달 가장자리 */}
        <circle cx="160" cy="160" r="100" fill="none"
                stroke="oklch(86% 0.06 180 / 0.45)" strokeWidth="0.5"
                mask="url(#crescent-shape)" />

        {/* 동반하는 별들 — 회전과 함께 돌아 깊이감 */}
        <g opacity="0.7">
          <circle cx="252" cy="84"  r="1.8" fill="oklch(96% 0.03 180)" />
          <circle cx="276" cy="178" r="1.2" fill="oklch(94% 0.03 180)" opacity="0.7" />
          <circle cx="226" cy="240" r="1.6" fill="oklch(96% 0.03 180)" opacity="0.85" />
          <circle cx="86"  cy="80"  r="1.0" fill="oklch(92% 0.03 180)" opacity="0.5" />
          <circle cx="56"  cy="200" r="1.4" fill="oklch(94% 0.03 180)" opacity="0.6" />
          <circle cx="180" cy="58"  r="0.9" fill="oklch(90% 0.03 180)" opacity="0.5" />
        </g>
      </g>

      <style>{`
        .mond-crescent-spin {
          animation: mond-crescent-rotate 80s linear infinite;
        }
        @keyframes mond-crescent-rotate {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @media (prefers-reduced-motion: reduce) {
          .mond-crescent-spin { animation: none; }
        }
      `}</style>
    </svg>
  );
}
