import React from "react";
import { useCurrentFrame } from "remotion";
import { scenes } from "../data/scenes";

interface CaptionLayerProps {
  style?: React.CSSProperties;
}

export const CaptionLayer: React.FC<CaptionLayerProps> = ({ style }) => {
  const frame = useCurrentFrame();

  // Find current scene caption
  const activeScene = scenes.find(s => frame >= s.start && frame < s.end);
  if (!activeScene || !activeScene.caption) return null;

  const captionText = activeScene.caption;
  const emphasisList = activeScene.emphasis || [];

  // Parse words and apply styles based on emphasis list
  const renderCaptionWords = () => {
    const words = captionText.split(" ");

    return words.map((word, idx) => {
      // Clean word from punctuation for match checks
      const cleanWord = word.replace(/[.,/#!$%^&*;:{}=\-_`~()]/g, "").toLowerCase();

      // Check if word (or part of it) matches any emphasis keywords
      const isEmphasized = emphasisList.some(emp =>
        cleanWord.includes(emp.toLowerCase()) || emp.toLowerCase().includes(cleanWord)
      ) ||
      // Add manual overrides for specific keywords we want highlighted
      ["seen", "signal", "fake", "proof", "94%", "clearer", "seen."].includes(cleanWord);

      return (
        <span
          key={idx}
          style={{
            color: isEmphasized ? "#00f0ff" : "#ffffff",
            textShadow: isEmphasized
              ? "0 0 15px rgba(0,240,255,0.8), 0 2px 10px rgba(0,0,0,0.6)"
              : "0 2px 10px rgba(0,0,0,0.8)",
            fontWeight: isEmphasized ? 900 : 700,
            fontSize: isEmphasized ? 46 : 40,
            transition: "all 0.1s ease-in-out",
          }}
        >
          {word}{" "}
        </span>
      );
    });
  };

  return (
    <div
      style={{
        position: "absolute",
        bottom: 150,
        left: "50%",
        transform: "translateX(-50%)",
        width: 900,
        minHeight: 120,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        zIndex: 150,
        pointerEvents: "none",
        background: "rgba(5, 5, 8, 0.65)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 20,
        padding: "16px 40px",
        boxShadow: "0 20px 40px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.04)",
        backdropFilter: "blur(12px)",
        ...style,
      }}
    >
      <p
        style={{
          margin: 0,
          fontFamily: '"Inter", "Helvetica Neue", Arial, sans-serif',
          lineHeight: 1.4,
          textTransform: "uppercase",
          letterSpacing: 1.5,
        }}
      >
        {renderCaptionWords()}
      </p>
    </div>
  );
};
