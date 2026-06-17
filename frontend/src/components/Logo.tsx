/**
 * 🌙 Mond 로고 컴포넌트 — 텍스트 + 달 이모지 (정식 PNG는 docs/assets에 있음)
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
      <span style={{ fontSize: 24, filter: "drop-shadow(0 0 8px rgba(124,140,255,0.6))" }}>
        🌙
      </span>
      {!collapsed && <span>Mond</span>}
    </div>
  );
}
