import { useEffect, useState } from "react";

/**
 * The signature element of VeriDoc: a small hand-drawn-feeling ring that
 * visualises confidence as a stamped, quantified thing rather than a bare
 * percentage. Used on field cards, document cards, and answer citations
 * so the whole product reads as one idea: trust, quantified.
 */
export default function ConfidenceRing({ value, size = 40, strokeWidth = 4 }) {
  const [animated, setAnimated] = useState(0);
  const pct = Math.round(value * 100);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(pct), 50);
    return () => clearTimeout(t);
  }, [pct]);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animated / 100) * circumference;

  const color = pct >= 90 ? "#7FA894" : pct >= 70 ? "#C98F5E" : "#D9A79C";
  const bg = pct >= 90 ? "#CFE3D8" : pct >= 70 ? "#E8D3B8" : "#E8D5D0";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={bg} strokeWidth={strokeWidth} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
        />
      </svg>
      <span
        className="absolute font-mono font-medium"
        style={{ fontSize: size * 0.28, color: "#3A3A42" }}
      >
        {pct}
      </span>
    </div>
  );
}
