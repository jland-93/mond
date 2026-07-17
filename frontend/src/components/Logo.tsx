/**
 * Mond 로고 컴포넌트 — 배경 투명 초승달 마크(public/logo-mark.png) 사용
 */

interface LogoProps {
  collapsed?: boolean;
}

export default function Logo({ collapsed = false }: LogoProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "16px 18px",
        borderBottom: "1px solid var(--mond-border)",
        fontWeight: 600,
        fontSize: 20,
        color: "var(--mond-text)",
      }}
    >
      <img
        src="/logo-mark.png"
        alt="Mond"
        width={28}
        height={28}
        style={{
          filter: "drop-shadow(0 0 8px rgba(124,140,255,0.4))",
        }}
      />
      {!collapsed && <span>Mond</span>}
    </div>
  );
}
