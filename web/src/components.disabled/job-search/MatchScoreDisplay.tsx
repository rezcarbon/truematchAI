'use client';

/**
 * Match score display component with color coding
 */

import React from 'react';
import { getMatchScoreColor, getMatchScoreLabel } from '@/lib/capability-matching';

interface MatchScoreDisplayProps {
  score: number; // 0-100
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showPercentage?: boolean;
}

export function MatchScoreDisplay({
  score,
  size = 'md',
  showLabel = true,
  showPercentage = true,
}: MatchScoreDisplayProps) {
  const color = getMatchScoreColor(score);
  const label = getMatchScoreLabel(score);

  const sizeStyles = {
    sm: {
      container: 'w-12 h-12',
      text: 'text-sm',
      textSize: 'text-xs',
    },
    md: {
      container: 'w-16 h-16',
      text: 'text-lg',
      textSize: 'text-xs',
    },
    lg: {
      container: 'w-20 h-20',
      text: 'text-2xl',
      textSize: 'text-sm',
    },
  };

  const style = sizeStyles[size];

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`${style.container} relative rounded-full flex items-center justify-center border-4`}
        style={{
          borderColor: color,
          background: `${color}15`,
        }}
      >
        <div className="text-center">
          <div className={`font-bold ${style.text}`} style={{ color }}>
            {showPercentage ? `${score}` : `${score}`}
          </div>
          {showPercentage && <div className={`${style.textSize} font-medium`}>%</div>}
        </div>

        {/* Circular progress ring */}
        <svg
          className="absolute inset-0 transform -rotate-90"
          viewBox="0 0 100 100"
          style={{
            filter: 'drop-shadow(0 0 2px rgba(0,0,0,0.05))',
          }}
        >
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={`${color}30`}
            strokeWidth="3"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={`${2.827 * score} ${282.7}`}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dasharray 0.5s ease',
            }}
          />
        </svg>
      </div>

      {showLabel && (
        <div className="text-center">
          <div
            className="text-xs font-semibold uppercase tracking-wide"
            style={{ color }}
          >
            {label}
          </div>
        </div>
      )}
    </div>
  );
}
