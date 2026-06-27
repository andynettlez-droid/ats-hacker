import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface SignalMascotProps {
  expression?: "neutral" | "focused" | "happy";
  dissolveProgress?: number; // 0 to 1
  logoMode?: boolean;         // if true, render smaller compact version for branding
  style?: React.CSSProperties;
}

export const SignalMascot: React.FC<SignalMascotProps> = ({
  expression = "neutral",
  dissolveProgress = 0,
  logoMode = false,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Pulse effect for core
  const corePulse = Math.sin(frame * 0.08) * 0.08 + 1;

  // Calculate coordinates of orbit particles over time
  const getOrbitPosition = (
    rx: number,
    ry: number,
    angleDeg: number,
    speed: number,
    offset: number = 0
  ) => {
    const theta = (frame * speed + offset) % (2 * Math.PI);
    const x = rx * Math.cos(theta);
    const y = ry * Math.sin(theta);
    const rad = (angleDeg * Math.PI) / 180;

    // Rotate 2D coordinates
    const rotX = x * Math.cos(rad) - y * Math.sin(rad);
    const rotY = x * Math.sin(rad) + y * Math.cos(rad);

    return { x: rotX, y: rotY };
  };

  // Three distinct orbits
  const orbit1 = getOrbitPosition(logoMode ? 60 : 120, logoMode ? 20 : 40, 30, 0.04);
  const orbit2 = getOrbitPosition(logoMode ? 65 : 130, logoMode ? 22 : 45, -45, -0.06, Math.PI / 2);
  const orbit3 = getOrbitPosition(logoMode ? 55 : 110, logoMode ? 18 : 35, 75, 0.05, Math.PI);

  // Dissolve particle positions
  const numParticles = 40;
  const particles = Array.from({ length: numParticles }).map((_, i) => {
    const angle = (i * (2 * Math.PI)) / numParticles + (i * 13.5);
    const baseDistance = logoMode ? 40 : 80;
    // Spring-based explosion outwards
    const springExp = spring({
      frame: Math.max(0, frame - 10), // slight delay
      fps,
      config: { damping: 12, mass: 0.8 },
    });

    const distance = baseDistance + dissolveProgress * 600 + springExp * dissolveProgress * 100;
    const px = Math.cos(angle) * distance;
    const py = Math.sin(angle) * distance;
    const size = interpolate(dissolveProgress, [0, 0.8, 1], [logoMode ? 3 : 6, logoMode ? 2 : 4, 0], {
      extrapolateRight: "clamp",
    });
    const opacity = interpolate(dissolveProgress, [0, 0.2, 0.8, 1], [1, 1, 0.4, 0]);

    return { x: px, y: py, size, opacity };
  });

  // Mascot scale/opacity during dissolve
  const mascotScale = interpolate(dissolveProgress, [0, 0.2, 0.5, 1], [1, 0.9, 0.4, 0]);
  const mascotOpacity = interpolate(dissolveProgress, [0, 0.4, 1], [1, 0.8, 0]);

  // Blink logic: blink every 150 frames (5s) for 6 frames
  const blinkCycle = 150;
  const blinkFrame = frame % blinkCycle;
  const isBlinking = blinkFrame >= 140 && blinkFrame <= 146;
  const eyeScaleY = isBlinking ? 0.1 : 1;

  // Face SVG path based on expression
  const renderEyes = () => {
    const size = logoMode ? 6 : 12;
    const spacing = logoMode ? 12 : 24;
    const yOffset = logoMode ? -3 : -6;

    if (expression === "happy") {
      // Curved arches for happy face
      return (
        <g stroke="#00f0ff" strokeWidth={logoMode ? 2.5 : 5} fill="none" strokeLinecap="round">
          {/* Left Eye */}
          <path d={`M ${-spacing - size/2} ${yOffset + size/4} Q ${-spacing} ${yOffset - size/2} ${-spacing + size/2} ${yOffset + size/4}`} />
          {/* Right Eye */}
          <path d={`M ${spacing - size/2} ${yOffset + size/4} Q ${spacing} ${yOffset - size/2} ${spacing + size/2} ${yOffset + size/4}`} />
        </g>
      );
    }

    if (expression === "focused") {
      // Slanted lines or small high-tech bars
      return (
        <g stroke="#00f0ff" strokeWidth={logoMode ? 2 : 4} fill="none" strokeLinecap="round">
          {/* Left Eye */}
          <line x1={-spacing - size/2} y1={yOffset - size/4} x2={-spacing + size/2} y2={yOffset + size/4} />
          {/* Right Eye */}
          <line x1={spacing - size/2} y1={yOffset + size/4} x2={spacing + size/2} y2={yOffset - size/4} />
        </g>
      );
    }

    // Neutral default blinking eyes
    return (
      <g fill="#00f0ff">
        <ellipse cx={-spacing} cy={yOffset} rx={logoMode ? 3.5 : 7} ry={logoMode ? 5 : 10 * eyeScaleY} style={{ filter: "drop-shadow(0 0 4px #00f0ff)" }} />
        <ellipse cx={spacing} cy={yOffset} rx={logoMode ? 3.5 : 7} ry={logoMode ? 5 : 10 * eyeScaleY} style={{ filter: "drop-shadow(0 0 4px #00f0ff)" }} />
      </g>
    );
  };

  const mainSize = logoMode ? 160 : 360;

  return (
    <div
      style={{
        position: "relative",
        width: mainSize,
        height: mainSize,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        ...style,
      }}
    >
      {/* ------------------------------------------------------------- */}
      {/* 1. Mascot main core & orbits (fades out during dissolve) */}
      {/* ------------------------------------------------------------- */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${mascotScale})`,
          opacity: mascotOpacity,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {/* Core Outer Aura Glow */}
        <div
          style={{
            position: "absolute",
            width: logoMode ? 60 : 120,
            height: logoMode ? 60 : 120,
            background: "radial-gradient(circle, rgba(0,240,255,0.4) 0%, rgba(0,100,255,0.15) 50%, rgba(0,0,0,0) 80%)",
            filter: "blur(20px)",
            borderRadius: "50%",
            transform: `scale(${corePulse})`,
          }}
        />

        {/* Central SVG Canvas for orbits, core, face */}
        <svg
          width="100%"
          height="100%"
          viewBox={`-${mainSize / 2} -${mainSize / 2} ${mainSize} ${mainSize}`}
          style={{ overflow: "visible" }}
        >
          <defs>
            <radialGradient id="coreGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="35%" stopColor="#00f0ff" />
              <stop offset="70%" stopColor="#0055ff" />
              <stop offset="100%" stopColor="#0a0a20" stopOpacity="0" />
            </radialGradient>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation={logoMode ? 3 : 6} result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Core Body Sphere */}
          <circle
            cx="0"
            cy="0"
            r={logoMode ? 22 : 44}
            fill="url(#coreGrad)"
            style={{ filter: "url(#glow)" }}
          />

          {/* Mascot Face */}
          {renderEyes()}

          {/* Orbit Rings (Tilt ellipses matching 2D coordinate calculations) */}
          <g stroke="rgba(0, 240, 255, 0.25)" strokeWidth={logoMode ? 1.5 : 2} fill="none">
            {/* Orbit 1 Ellipse */}
            <ellipse rx={logoMode ? 60 : 120} ry={logoMode ? 20 : 40} transform="rotate(30)" />
            {/* Orbit 2 Ellipse */}
            <ellipse rx={logoMode ? 65 : 130} ry={logoMode ? 22 : 45} transform="rotate(-45)" />
            {/* Orbit 3 Ellipse */}
            <ellipse rx={logoMode ? 55 : 110} ry={logoMode ? 18 : 35} transform="rotate(75)" />
          </g>

          {/* Gliding Orbit Particles */}
          <g fill="#00f0ff" filter="url(#glow)">
            <circle cx={orbit1.x} cy={orbit1.y} r={logoMode ? 2.5 : 5} />
            <circle cx={orbit2.x} cy={orbit2.y} r={logoMode ? 3.5 : 7} />
            <circle cx={orbit3.x} cy={orbit3.y} r={logoMode ? 2 : 4} />
          </g>
        </svg>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 2. Particle dissolution (explodes outwards during dissolve) */}
      {/* ------------------------------------------------------------- */}
      {dissolveProgress > 0 && (
        <svg
          style={{
            position: "absolute",
            inset: 0,
            overflow: "visible",
            pointerEvents: "none",
          }}
          viewBox={`-${mainSize / 2} -${mainSize / 2} ${mainSize} ${mainSize}`}
        >
          <g fill="#00f0ff" filter="url(#glow)">
            {particles.map((p, idx) => (
              <circle
                key={idx}
                cx={p.x}
                cy={p.y}
                r={p.size}
                opacity={p.opacity}
              />
            ))}
          </g>
        </svg>
      )}
    </div>
  );
};
