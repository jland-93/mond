/**
 * 🛡️ Moon3DSafe — Moon3D 안전 wrapper
 *
 * Three.js 로드 실패 / WebGL 미지원 / 컴포넌트 에러 시 fallback(2D)으로 자동 전환.
 * 페이지 전체가 흰 화면이 되는 사고 방지.
 */

import { Suspense, lazy, Component, type ReactNode } from "react";

const Moon3D = lazy(() => import("./Moon3D"));

interface BoundaryProps {
  fallback: ReactNode;
  children: ReactNode;
}
interface BoundaryState {
  failed: boolean;
}

class Boundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(err: unknown) {
    // eslint-disable-next-line no-console
    console.warn("[Moon3DSafe] Three.js failed, falling back:", err);
  }
  render() {
    if (this.state.failed) return <>{this.props.fallback}</>;
    return <>{this.props.children}</>;
  }
}

export interface Moon3DSafeProps {
  size?: number;
  fallback: ReactNode;
  className?: string;
}

export default function Moon3DSafe({ size = 280, fallback, className }: Moon3DSafeProps) {
  // WebGL 미지원이면 fallback 즉시
  const hasWebGL =
    typeof window !== "undefined" &&
    (() => {
      try {
        const c = document.createElement("canvas");
        return !!(c.getContext("webgl") || c.getContext("experimental-webgl"));
      } catch {
        return false;
      }
    })();

  if (!hasWebGL) return <>{fallback}</>;

  return (
    <Boundary fallback={fallback}>
      <Suspense fallback={<>{fallback}</>}>
        <div className={className} style={{ width: size, height: size }}>
          <Moon3D size={size} />
        </div>
      </Suspense>
    </Boundary>
  );
}
