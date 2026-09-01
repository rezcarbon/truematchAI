'use client';

import React, { useMemo, useCallback } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight, Calendar, TrendingUp, BookOpen } from 'lucide-react';
import type { Assessment } from '@/lib/types';

export interface AssessmentSummaryProps {
  assessment: Assessment;
  className?: string;
  onViewAnalysis?: () => void;
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const getScoreColor = (score: number): string => {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 60) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-600 dark:text-red-400';
};

const getScoreBgColor = (score: number): string => {
  if (score >= 80) return 'bg-green-100 dark:bg-green-900';
  if (score >= 60) return 'bg-amber-100 dark:bg-amber-900';
  return 'bg-red-100 dark:bg-red-900';
};

export const AssessmentSummary: React.FC<AssessmentSummaryProps> = React.memo(
  ({ assessment, className = '', onViewAnalysis }) => {
    const handleViewAnalysis = useCallback(() => {
      onViewAnalysis?.();
    }, [onViewAnalysis]);

    const topStrengths = useMemo(() => {
      return assessment.capabilityScore.components
        ?.filter((c) => c.score >= 70)
        .sort((a, b) => b.score - a.score)
        .slice(0, 3) || [];
    }, [assessment.capabilityScore.components]);

    const topGaps = useMemo(() => {
      return assessment.capabilityScore.components
        ?.filter((c) => c.score < 70)
        .sort((a, b) => a.score - b.score)
        .slice(0, 2) || [];
    }, [assessment.capabilityScore.components]);

    const traditionalScoreBg = useMemo(
      () => getScoreBgColor(assessment.traditionalScore),
      [assessment.traditionalScore]
    );

    const semanticScoreBg = useMemo(
      () =>
        assessment.semanticScore
          ? getScoreBgColor(assessment.semanticScore)
          : '',
      [assessment.semanticScore]
    );

    const capabilityScoreBg = useMemo(
      () => getScoreBgColor(assessment.capabilityScore.overall),
      [assessment.capabilityScore.overall]
    );

    return (
      <Card className={className}>
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <CardTitle className="text-xl">Latest Assessment</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {assessment.positionTitle}
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Calendar className="w-4 h-4" />
              <span>{formatDate(assessment.createdAt)}</span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Score Grid */}
          <div className="grid grid-cols-3 gap-3">
            {/* Traditional Score */}
            <div className={`p-3 rounded-lg ${traditionalScoreBg}`}>
              <div className="text-xs text-muted-foreground font-medium mb-1">
                Traditional
              </div>
              <div
                className={`text-2xl font-bold ${getScoreColor(assessment.traditionalScore)}`}
              >
                {assessment.traditionalScore}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Keyword Match</p>
            </div>

            {/* Semantic Score */}
            {assessment.semanticScore !== undefined && (
              <div className={`p-3 rounded-lg ${semanticScoreBg}`}>
                <div className="text-xs text-muted-foreground font-medium mb-1">
                  Semantic
                </div>
                <div
                  className={`text-2xl font-bold ${getScoreColor(assessment.semanticScore)}`}
                >
                  {assessment.semanticScore}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Concept Match</p>
              </div>
            )}

            {/* Capability Score */}
            <div className={`p-3 rounded-lg ${capabilityScoreBg}`}>
              <div className="text-xs text-muted-foreground font-medium mb-1">
                Capability
              </div>
              <div
                className={`text-2xl font-bold ${getScoreColor(assessment.capabilityScore.overall)}`}
              >
                {assessment.capabilityScore.overall}
              </div>
              <p className="text-xs text-muted-foreground mt-1">TrueMatch</p>
            </div>
          </div>

          {/* Strengths */}
          {topStrengths.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />
                <h3 className="text-sm font-semibold">Your Strengths</h3>
              </div>
              <div className="space-y-2">
                {topStrengths.map((strength, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-green-50 dark:bg-green-950 rounded"
                  >
                    <span className="text-sm text-green-900 dark:text-green-200">
                      {strength.label}
                    </span>
                    <Badge
                      variant="secondary"
                      className="bg-green-200 text-green-800 dark:bg-green-800 dark:text-green-200"
                    >
                      {strength.score}%
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gaps */}
          {topGaps.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <BookOpen className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                <h3 className="text-sm font-semibold">Learning Opportunities</h3>
              </div>
              <div className="space-y-2">
                {topGaps.map((gap, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-amber-50 dark:bg-amber-950 rounded"
                  >
                    <span className="text-sm text-amber-900 dark:text-amber-200">
                      {gap.label}
                    </span>
                    <Badge
                      variant="secondary"
                      className="bg-amber-200 text-amber-800 dark:bg-amber-800 dark:text-amber-200"
                    >
                      {gap.score}%
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Button */}
          <Button
            className="w-full"
            onClick={handleViewAnalysis}
            variant="default"
          >
            View Full Analysis
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>

          {/* Link to detailed assessment if available */}
          {assessment.id && (
            <Button
              className="w-full"
              variant="outline"
              asChild
            >
              <Link href={`/candidate/assessment/${assessment.id}`}>
                View Assessment Details
              </Link>
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }
);

AssessmentSummary.displayName = 'AssessmentSummary';
