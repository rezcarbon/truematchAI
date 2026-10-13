"use client";
import * as React from "react";
import { cn } from "@/lib/utils";
import { scoreTier } from "@/lib/utils";

// Pure SVG radial gauge primitive. Renders a 0..100 value supplied by the
// caller (ultimately the backend). It performs no thresholding decisions —
// the tier mapping is presentational color only.
export function Gauge({
  value,
  size = 120,
  label,
  className,
}: {
  value: number;
  size?: number;
  label?: string;
  className?: string;
}) {
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = circumference - (clamped / 100) * circumference;
  const tier = scoreTier(clamped);
  const color =
    tier === "high"
      ? "hsl(var(--success))"
      : tier === "mid"
      ? "hsl(var(--warning))"
      : "hsl(var(--destructive))";

  return (
    <div
      className={cn("relative inline-flex items-center justify-center", className)}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="hsl(var(--muted))"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold tabular-nums">{Math.round(clamped)}</span>
        {label && <span className="text-xs text-muted-foreground">{label}</span>}
      </div>
    </div>
  );
}
