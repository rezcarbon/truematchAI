'use client';

import React, { useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  CheckCircle2,
  Circle,
  Lock,
  ChevronRight,
  Calendar,
  Award,
} from 'lucide-react';

export interface LearningPathStep {
  id: string;
  title: string;
  description: string;
  status: 'completed' | 'current' | 'locked' | 'upcoming';
  estimatedTime: number; // in minutes
  completedAt?: string;
  resources?: {
    title: string;
    url: string;
  }[];
}

export interface LearningPathProps {
  title: string;
  description?: string;
  steps: LearningPathStep[];
  currentStepIndex?: number;
  onStepClick?: (stepId: string, stepIndex: number) => void;
  onCompleteStep?: (stepId: string, stepIndex: number) => void;
  className?: string;
}

const StepIcon: React.FC<{
  status: LearningPathStep['status'];
  isCurrentStep: boolean;
}> = React.memo(({ status, isCurrentStep }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-6 h-6 text-green-500" />;
    case 'current':
      return (
        <div className="relative w-6 h-6">
          <Circle className="w-6 h-6 text-primary animate-pulse" fill="currentColor" />
          <Circle className="w-6 h-6 text-primary absolute inset-0" strokeWidth={2} />
        </div>
      );
    case 'locked':
      return <Lock className="w-6 h-6 text-muted-foreground" />;
    default:
      return <Circle className="w-6 h-6 text-muted-foreground" />;
  }
});

StepIcon.displayName = 'StepIcon';

export const LearningPath: React.FC<LearningPathProps> = React.memo(
  ({
    title,
    description,
    steps,
    currentStepIndex = 0,
    onStepClick,
    onCompleteStep,
    className = '',
  }) => {
    const completedCount = useMemo(
      () => steps.filter((s) => s.status === 'completed').length,
      [steps]
    );

    const progressPercentage = useMemo(
      () => Math.round((completedCount / steps.length) * 100),
      [completedCount, steps.length]
    );

    const totalTime = useMemo(
      () => steps.reduce((sum, step) => sum + step.estimatedTime, 0),
      [steps]
    );

    const handleStepClick = useCallback(
      (stepId: string, stepIndex: number) => {
        if (steps[stepIndex].status !== 'locked') {
          onStepClick?.(stepId, stepIndex);
        }
      },
      [steps, onStepClick]
    );

    const handleCompleteStep = useCallback(
      (e: React.MouseEvent, stepId: string, stepIndex: number) => {
        e.stopPropagation();
        onCompleteStep?.(stepId, stepIndex);
      },
      [onCompleteStep]
    );

    return (
      <Card className={`w-full ${className}`}>
        <CardHeader className="pb-4">
          <div className="space-y-4">
            <div>
              <CardTitle className="text-2xl mb-2">{title}</CardTitle>
              {description && (
                <p className="text-sm text-muted-foreground">{description}</p>
              )}
            </div>

            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-foreground">
                  Progress: {completedCount} of {steps.length}
                </span>
                <span className="text-muted-foreground">{progressPercentage}%</span>
              </div>
              <Progress value={progressPercentage} className="h-2" />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  <span>Total time</span>
                </div>
                <p className="text-lg font-semibold">{totalTime} min</p>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Award className="w-4 h-4" />
                  <span>Completion</span>
                </div>
                <p className="text-lg font-semibold">{progressPercentage}%</p>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="space-y-0">
            {steps.map((step, index) => {
              const isCurrentStep = index === currentStepIndex;
              const isClickable = step.status !== 'locked';

              return (
                <div key={step.id}>
                  {/* Connector line */}
                  {index < steps.length - 1 && (
                    <div
                      className={`ml-3 w-0.5 h-8 ${
                        step.status === 'completed'
                          ? 'bg-green-500'
                          : 'bg-muted-foreground/20'
                      }`}
                    />
                  )}

                  {/* Step container */}
                  <div
                    className={`relative pl-12 pb-6 cursor-pointer group transition-colors ${
                      isClickable
                        ? 'hover:bg-secondary/50'
                        : 'cursor-not-allowed opacity-60'
                    } p-4 rounded-lg -ml-4 -px-4`}
                    onClick={() => handleStepClick(step.id, index)}
                    role="button"
                    tabIndex={isClickable ? 0 : -1}
                    onKeyDown={(e) => {
                      if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
                        handleStepClick(step.id, index);
                      }
                    }}
                  >
                    {/* Icon - absolute positioned */}
                    <div className="absolute left-0 top-5">
                      <StepIcon
                        status={step.status}
                        isCurrentStep={isCurrentStep}
                      />
                    </div>

                    {/* Content */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold text-base">
                          Step {index + 1}: {step.title}
                        </h3>
                        {isCurrentStep && (
                          <Badge
                            variant="default"
                            className="text-xs font-medium"
                          >
                            Current
                          </Badge>
                        )}
                        {step.status === 'completed' && (
                          <Badge
                            variant="secondary"
                            className="text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                          >
                            Completed
                          </Badge>
                        )}
                      </div>

                      <p className="text-sm text-muted-foreground">
                        {step.description}
                      </p>

                      {/* Meta info */}
                      <div className="flex items-center justify-between text-xs text-muted-foreground pt-2">
                        <span>{step.estimatedTime} minutes</span>
                        {step.completedAt && (
                          <span>
                            Completed{' '}
                            {new Date(step.completedAt).toLocaleDateString()}
                          </span>
                        )}
                      </div>

                      {/* Resources */}
                      {step.resources && step.resources.length > 0 && (
                        <div className="flex flex-wrap gap-2 pt-2">
                          {step.resources.map((resource, i) => (
                            <Button
                              key={i}
                              variant="ghost"
                              size="sm"
                              className="text-xs h-7"
                              asChild
                            >
                              <a
                                href={resource.url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {resource.title}
                                <ChevronRight className="w-3 h-3 ml-1" />
                              </a>
                            </Button>
                          ))}
                        </div>
                      )}

                      {/* Complete button for current step */}
                      {isCurrentStep && step.status === 'current' && (
                        <Button
                          size="sm"
                          className="mt-3"
                          onClick={(e) =>
                            handleCompleteStep(e, step.id, index)
                          }
                        >
                          Mark as Complete
                          <CheckCircle2 className="w-4 h-4 ml-2" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    );
  }
);

LearningPath.displayName = 'LearningPath';
