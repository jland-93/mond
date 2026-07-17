/**
 * 🌕 Moon3D — Three.js 기반 실사 달
 *
 * 실사 달 텍스처(NASA 출처 lunar color map)를 sphere에 입히고,
 * 같은 텍스처를 bumpMap으로 재사용해 분화구 요철을 살린다.
 * 조명은 카메라 정면 약간 위/좌에 **고정** → 보름달에 가까운 은은한 명암(terminator).
 * sphere는 아주 느리게 자전해 분화구가 흘러가는 입체감만 준다(공전 조명 없음).
 */

import { Canvas, useFrame, useLoader } from "@react-three/fiber";
import { Suspense, useRef } from "react";
import * as THREE from "three";

function MoonSphere() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((_state, delta) => {
    // 느린 자전만 — 지구본 autoRotate 같은 차분한 움직임
    if (meshRef.current) meshRef.current.rotation.y += delta * 0.045;
  });

  const texture = useLoader(THREE.TextureLoader, "/moon/moon_color.jpg");

  return (
    // 살짝 기울여 극(pole)이 정면을 향하지 않게 — 자연스러운 시점
    <mesh ref={meshRef} rotation={[0.12, 0, 0.08]}>
      <sphereGeometry args={[1, 128, 128]} />
      {/* colorSpace/anisotropy는 텍스처 직접 mutation 대신 선언적으로 설정 */}
      <meshStandardMaterial
        map={texture}
        map-colorSpace={THREE.SRGBColorSpace}
        map-anisotropy={4}
        bumpMap={texture}
        bumpScale={0.02}
        roughness={1}
        metalness={0}
      />
    </mesh>
  );
}

function AtmosphereGlow() {
  // 달은 대기가 없지만, 어두운 히어로 위에서 은은한 달무리(halo)로 읽히게 아주 옅게.
  return (
    <mesh>
      <sphereGeometry args={[1.25, 48, 48]} />
      <meshBasicMaterial
        color="#cfe0ff"
        transparent
        opacity={0.05}
        side={THREE.BackSide}
        depthWrite={false}
      />
    </mesh>
  );
}

export interface Moon3DProps {
  size?: number;
  className?: string;
}

export default function Moon3D({ size = 320, className }: Moon3DProps) {
  return (
    <div className={className} style={{ width: size, height: size, position: "relative" }}>
      {/* 부드러운 원형 달무리 — 마스크된 canvas 가장자리를 히어로 배경에 자연스럽게 녹임 */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: -size * 0.28,
          background:
            "radial-gradient(circle at center, oklch(80% 0.06 230 / 0.18) 0%, transparent 60%)",
          pointerEvents: "none",
        }}
      />
      <Canvas
        camera={{ position: [0, 0, 3.0], fov: 38 }}
        gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
        dpr={[1, 2]}
        style={{
          background: "transparent",
          // 정사각 canvas의 네 모서리를 원형으로 잘라내 사각 틀 제거
          WebkitMaskImage:
            "radial-gradient(circle at 50% 50%, #000 66%, transparent 72%)",
          maskImage: "radial-gradient(circle at 50% 50%, #000 66%, transparent 72%)",
        }}
      >
        {/* 어두운 면도 살짝 보이는 earthshine 느낌의 옅은 환경광 */}
        <ambientLight intensity={0.18} color="#8fa8c8" />
        {/* 정면 약간 위/좌 고정 조명 — 부드러운 gibbous terminator */}
        <directionalLight position={[-1.4, 1.1, 3]} intensity={2.4} color="#fff6ea" />
        <AtmosphereGlow />
        <Suspense fallback={null}>
          <MoonSphere />
        </Suspense>
      </Canvas>
    </div>
  );
}
