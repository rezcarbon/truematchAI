'use client';

import React, { useEffect, useState } from 'react';

interface QualityScoreGaugeProps {
  score: number; // 0-100
}

export default function QualityScoreGauge({ score }: QualityScoreGaugeProps) {
  const [displayScore, setDisplayScore] = useState(0);

  // Animate the score
  useEffect(() => {
    if (score === 0) {
      setDisplayScore(0);
      return;
    }

    let current = 0;
    const increment = score / 30; // Animate over ~30 frames
    const interval = setInterval(() => {
      current += increment;
      if (current >= score) {
        setDisplayScore(score);
        clearInterval(interval);
      } else {
        setDisplayScore(Math.floor(current));
      }
    }, 30);

    return () => clearInterval(interval);
  }, [score]);

  const getColorClass = (value: number) => {
    if (value >= 80) return 'text-green-600';
    if (value >= 60) return 'text-yellow-600';
    if (value >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getGaugeColor = (value: number) => {
    if (value >= 80) return '#10b981'; // green
    if (value >= 60) return '#eab308'; // yellow
    if (value >= 40) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (displayScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32">
        <svg
          className="w-32 h-32 transform -rotate-90"
          viewBox="0 0 120 120"
        >
          {/* Background circle */}
          <circle
            cx="60"
            cy="60"
            r="45"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="8"
          />

          {/* Progress circle */}
          <circle
            cx="60"
            cy="60"
            r="45"
            fill="none"
            stroke={getGaugeColor(displayScore)}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-300"
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-4xl font-bold ${getColorClass(displayScore)}`}>
            {displayScore}
          </span>
          <span className="text-xs text-gray-600">Score</span>
        </div>
      </div>

      {/* Label */}
      <div className="mt-6 text-center">
        <p className="text-sm font-medium text-gray-900">
          {displayScore >= 80 && 'Excellent'}
          {displayScore >= 60 && displayScore < 80 && 'Good'}
          {displayScore >= 40 && displayScore < 60 && 'Fair'}
          {displayScore < 40 && 'Needs Improvement'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {displayScore === 100 && 'Perfect job description!'}
          {displayScore >= 80 && displayScore < 100 && 'Minor improvements available'}
          {displayScore >= 60 && displayScore < 80 && 'Some improvements recommended'}
          {displayScore >= 40 && displayScore < 60 &&
            'Several improvements needed'}
          {displayScore < 40 && 'Significant improvements needed'}
        </p>
      </div>
    </div>
  );
}
