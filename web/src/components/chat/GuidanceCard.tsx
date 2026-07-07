'use client';

import React, { useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight, BookOpen, Github, Users, Clock, ExternalLink } from 'lucide-react';

export type DifficultyLevel = 'Beginner' | 'Intermediate' | 'Advanced';

export interface GuidanceStep {
  number: number;
  title: string;
  description: string;
  estimatedTime: number; // in minutes
  resources?: GuidanceResource[];
}

export interface GuidanceResource {
  title: string;
  url: string;
  type: 'course' | 'github' | 'community' | 'docs' | 'article';
}

export interface GuidanceCardProps {
  title: string;
  description: string;
  steps: GuidanceStep[];
  difficulty: DifficultyLevel;
  totalTime?: number; // in minutes
  onStepClick?: (stepNumber: number) => void;
  className?: string;
}

const RESOURCE_ICONS: Record<GuidanceResource['type'], React.ReactNode> = {
  course: <BookOpen className="w-4 h-4" />,
  github: <Github className="w-4 h-4" />,
  community: <Users className="w-4 h-4" />,
  docs: <BookOpen className="w-4 h-4" />,
  article: <BookOpen className="w-4 h-4" />,
};

const DIFFICULTY_COLORS: Record<DifficultyLevel, string> = {
  Beginner: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  Intermediate: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  Advanced: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export const GuidanceCard: React.FC<GuidanceCardProps> = React.memo(
  ({
    title,
    description,
    steps,
    difficulty,
    totalTime,
    onStepClick,
    className = '',
  }) => {
    const calculatedTotalTime = useMemo(() => {
      if (totalTime) return totalTime;
      return steps.reduce((sum, step) => sum + step.estimatedTime, 0);
    }, [steps, totalTime]);

    const handleResourceClick = useCallback(
      (e: React.MouseEvent<HTMLAnchorElement>, url: string) => {
        e.preventDefault();
        window.open(url, '_blank', 'noopener,noreferrer');
      },
      []
    );

    const handleStepClick = useCallback(
      (stepNumber: number) => {
        onStepClick?.(stepNumber);
      },
      [onStepClick]
    );

    return (
      <Card className={`w-full overflow-hidden ${className}`}>
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <CardTitle className="text-xl mb-2">{title}</CardTitle>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
            <Badge
              variant="secondary"
              className={`whitespace-nowrap ${DIFFICULTY_COLORS[difficulty]}`}
            >
              {difficulty}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Header Stats */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock className="w-4 h-4" />
              <span>{calculatedTotalTime} min total</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <span className="font-medium">{steps.length} steps</span>
            </div>
          </div>

          {/* Steps */}
          <div className="space-y-4">
            {steps.map((step, index) => (
              <div
                key={step.number}
                className="space-y-3 pb-4 border-b last:border-b-0 last:pb-0"
              >
                {/* Step header */}
                <div
                  className="flex items-start gap-4 cursor-pointer group"
                  onClick={() => handleStepClick(step.number)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handleStepClick(step.number);
                    }
                  }}
                >
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-semibold text-sm flex-shrink-0 group-hover:shadow-lg transition-shadow">
                    {step.number}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-base group-hover:text-primary transition-colors">
                        {step.title}
                      </h3>
                      {index < steps.length - 1 && (
                        <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {step.description}
                    </p>
                  </div>
                </div>

                {/* Time estimate */}
                <div className="ml-12">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    <span>~{step.estimatedTime} minutes</span>
                  </div>
                </div>

                {/* Resources */}
                {step.resources && step.resources.length > 0 && (
                  <div className="ml-12">
                    <div className="space-y-2">
                      {step.resources.map((resource, resourceIndex) => (
                        <a
                          key={resourceIndex}
                          href={resource.url}
                          onClick={(e) => handleResourceClick(e, resource.url)}
                          className="flex items-center gap-3 p-2 rounded-md bg-secondary/50 hover:bg-secondary transition-colors group text-sm"
                        >
                          <span className="text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0">
                            {RESOURCE_ICONS[resource.type]}
                          </span>
                          <span className="flex-1 truncate text-foreground group-hover:text-primary transition-colors">
                            {resource.title}
                          </span>
                          <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* CTA Button */}
          <Button className="w-full mt-4" size="lg">
            Start Learning Path
          </Button>
        </CardContent>
      </Card>
    );
  }
);

GuidanceCard.displayName = 'GuidanceCard';
