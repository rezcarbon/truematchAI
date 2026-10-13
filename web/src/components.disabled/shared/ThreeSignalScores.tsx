'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

export interface ScoreGaugeProps {
  label: string;
  score: number; // 0-100
  maxScore?: number;
  delta?: number; // Change from previous assessment
  description?: string;
  icon?: React.ReactNode;
}

export interface ThreeSignalScoresProps {
  traditional: ScoreGaugeProps;
  semantic: ScoreGaugeProps;
  capability: ScoreGaugeProps;
  className?: string;
}

const getScoreColor = (
  score: number
): { text: string; bg: string; border: string } => {
  if (score >= 80) {
    return {
      text: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-100 dark:bg-green-900',
      border: 'border-green-200 dark:border-green-800',
    };
  }
  if (score >= 60) {
    return {
      text: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-100 dark:bg-amber-900',
      border: 'border-amber-200 dark:border-amber-800',
    };
  }
  return {
    text: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900',
    border: 'border-red-200 dark:border-red-800',
  };
};

const GaugeIndicator: React.FC<{
  score: number;
  size?: 'small' | 'large';
}> = React.memo(({ score, size = 'large' }) => {
  const circumference = size === 'large' ? 251.2 : 125.6; // 2 * PI * r
  const radius = size === 'large' ? 40 : 20;
  const offset = circumference - (score / 100) * circumference;

  const colors = getScoreColor(score);

  return (
    <div className="relative flex items-center justify-center">
      <svg
        width={size === 'large' ? 120 : 60}
        height={size === 'large' ? 120 : 60}
        viewBox="0 0 120 120"
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          className="text-secondary"
        />

        {/* Progress circle */}
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`${colors.text} transition-all`}
        />
      </svg>

      {/* Score text */}
      <div className="absolute flex flex-col items-center justify-center">
        <span className={`${size === 'large' ? 'text-2xl' : 'text-lg'} font-bold ${colors.text}`}>
          {score}
        </span>
        <span className="text-xs text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
});

GaugeIndicator.displayName = 'GaugeIndicator';

const ScoreGauge: React.FC<ScoreGaugeProps & { large?: boolean }> = React.memo(
  ({ label, score, delta, description, icon, large = true }) => {
    const colors = useMemo(() => getScoreColor(score), [score]);

    const DeltaIcon = useMemo(() => {
      if (delta === undefined) return null;
      if (delta > 0) return ArrowUp;
      if (delta < 0) return ArrowDown;
      return Minus;
    }, [delta]);

    const deltaColor = useMemo(() => {
      if (delta === undefined) return 'text-muted-foreground';
      if (delta > 0) return 'text-green-600 dark:text-green-400';
      if (delta < 0) return 'text-red-600 dark:text-red-400';
      return 'text-muted-foreground';
    }, [delta]);

    return (
      <div className={`flex flex-col items-center gap-3 p-4 rounded-lg border ${colors.border} ${colors.bg}`}>
        {/* Gauge */}
        <GaugeIndicator score={score} size={large ? 'large' : 'small'} />

        {/* Label and delta */}
        <div className="text-center">
          <p className="text-sm font-semibold text-foreground">{label}</p>
          {delta !== undefined && (
            <div className={`flex items-center justify-center gap-1 mt-1 ${deltaColor}`}>
              {DeltaIcon && <DeltaIcon className="w-3 h-3" />}
              <span className="text-xs font-medium">
                {delta > 0 ? '+' : ''}{delta}
              </span>
            </div>
          )}
        </div>

        {/* Description */}
        {description && (
          <p className="text-xs text-muted-foreground text-center max-w-xs">
            {description}
          </p>
        )}
      </div>
    );
  }
);

ScoreGauge.displayName = 'ScoreGauge';

export const ThreeSignalScores: React.FC<ThreeSignalScoresProps> = React.memo(
  ({ traditional, semantic, capability, className = '' }) => {
    const averageScore = useMemo(
      () => {
        let sum = traditional.score + capability.score;
        let count = 2;

        if (semantic.score !== undefined) {
          sum += semantic.score;
          count += 1;
        }

        return Math.round(sum / count);
      },
      [traditional.score, semantic.score, capability.score]
    );

    return (
      <Card className={className}>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl">Assessment Scores</CardTitle>
            <Badge
              variant="default"
              className="text-lg px-3 py-1"
            >
              {averageScore}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Your multi-signal assessment breakdown
          </p>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <ScoreGauge
              label={traditional.label}
              score={traditional.score}
              delta={traditional.delta}
              description={traditional.description}
              large={true}
            />

            <ScoreGauge
              label={semantic.label}
              score={semantic.score}
              delta={semantic.delta}
              description={semantic.description}
              large={true}
            />

            <ScoreGauge
              label={capability.label}
              score={capability.score}
              delta={capability.delta}
              description={capability.description}
              large={true}
            />
          </div>

          {/* Summary info */}
          <div className="mt-6 space-y-3 p-4 bg-secondary/50 rounded-lg">
            <div className="text-sm">
              <p className="font-semibold mb-2">Signal Interpretation:</p>
              <ul className="space-y-2 text-xs text-muted-foreground">
                <li className="flex gap-2">
                  <span className="font-medium w-20">Traditional:</span>
                  <span>Keyword and ATS matching score</span>
                </li>
                <li className="flex gap-2">
                  <span className="font-medium w-20">Semantic:</span>
                  <span>Concept-level relevance and understanding</span>
                </li>
                <li className="flex gap-2">
                  <span className="font-medium w-20">Capability:</span>
                  <span>Demonstrated capability based on background</span>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
);

ThreeSignalScores.displayName = 'ThreeSignalScores';

export { ScoreGauge, GaugeIndicator };
