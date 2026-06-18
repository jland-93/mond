/**
 * View Transitions API — 페이지 전환 native feel
 *
 * Chrome 111+, Safari 18+, Firefox 144+ (2026 기준 전세계 ~93%).
 * 미지원 브라우저는 그냥 즉시 전환으로 안전 폴백.
 *
 * react-router-dom 6.28+의 unstable_viewTransition prop을 쓸 수도 있지만,
 * navigate() 호출 지점이 많은 우리 코드베이스에는 helper 한 개가 더 깨끗하다.
 */

type Navigator = () => void;

const supportsViewTransition = (): boolean => {
  if (typeof document === "undefined") return false;
  return typeof document.startViewTransition === "function";
};

const prefersReducedMotion = (): boolean => {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
};

/**
 * navigate() 또는 임의의 DOM 변경을 View Transition으로 감싼다.
 *
 * @example
 *   withTransition(() => navigate("/findings"));
 */
export function withTransition(fn: Navigator): void {
  if (!supportsViewTransition() || prefersReducedMotion()) {
    fn();
    return;
  }
  document.startViewTransition(() => {
    fn();
  });
}
