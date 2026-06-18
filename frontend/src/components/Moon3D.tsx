/**
 * 🌒 Moon3D — Three.js 기반 입체 초승달 (waxing crescent)
 *
 * sphere는 가만히 두고 **directional light**을 sphere 주위로 우방향(시계방향) 공전.
 * 빛이 비치는 lit 영역 = 초승달 silhouette → 시청자에게는 초승달이 회전하듯 보임.
 * sphere 자체도 천천히 자전해서 표면 분화구가 좌→우로 흘러가는 입체감.
 */

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function MoonSphere() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((_state, delta) => {
    if (meshRef.current) meshRef.current.rotation.y += delta * 0.06;
  });

  const texture = useMemo(() => {
    if (typeof document === "undefined") return null;
    const cvs = document.createElement("canvas");
    cvs.width = 1024;
    cvs.height = 512;
    const ctx = cvs.getContext("2d");
    if (!ctx) return null;
    ctx.fillStyle = "#c8d8d5";
    ctx.fillRect(0, 0, cvs.width, cvs.height);
    for (let i = 0; i < 220; i++) {
      const x = Math.random() * cvs.width;
      const y = Math.random() * cvs.height;
      const r = 4 + Math.random() * 28;
      const shade = 95 + Math.random() * 70;
      const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
      grad.addColorStop(0, `rgba(${shade - 30}, ${shade - 10}, ${shade}, 0.5)`);
      grad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
    for (let i = 0; i < 5; i++) {
      const x = Math.random() * cvs.width;
      const y = 80 + Math.random() * 350;
      const r = 70 + Math.random() * 130;
      const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
      grad.addColorStop(0, "rgba(70, 100, 110, 0.4)");
      grad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
    const tex = new THREE.CanvasTexture(cvs);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
  }, []);

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[1, 96, 96]} />
      <meshStandardMaterial
        map={texture ?? undefined}
        color="#dceae5"
        roughness={0.95}
        metalness={0.02}
        emissive="#0a1418"
        emissiveIntensity={0.05}
      />
    </mesh>
  );
}

function OrbitingLight() {
  const lightRef = useRef<THREE.DirectionalLight>(null);
  useFrame((state) => {
    if (!lightRef.current) return;
    // 18s 한 바퀴, 시계방향(우방향)
    const t = state.clock.elapsedTime * ((2 * Math.PI) / 18);
    const radius = 4;
    lightRef.current.position.set(Math.cos(t) * radius, 0.4, Math.sin(t) * radius);
  });
  return (
    <directionalLight
      ref={lightRef}
      position={[4, 0.4, 0.5]}
      intensity={3.2}
      color="#e6f3f0"
    />
  );
}

function AtmosphereGlow() {
  return (
    <mesh>
      <sphereGeometry args={[1.22, 48, 48]} />
      <meshBasicMaterial
        color="#7fc8c0"
        transparent
        opacity={0.07}
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
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: -size * 0.4,
          background:
            "radial-gradient(circle at center, oklch(82% 0.08 180 / 0.30) 0%, oklch(60% 0.10 250 / 0.16) 38%, transparent 68%)",
          pointerEvents: "none",
        }}
      />
      <Canvas
        camera={{ position: [0, 0, 3.0], fov: 38 }}
        gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
        dpr={[1, 2]}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.04} color="#5a8086" />
        <AtmosphereGlow />
        <OrbitingLight />
        <MoonSphere />
      </Canvas>
    </div>
  );
}
