'use client';

import React, { useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle2,
  Circle,
  ArrowRight,
  AlertCircle,
  FileText,
  Users,
  Briefcase,
  Gift,
  X,
} from 'lucide-react';

export type ApplicationStage =
  | 'applied'
  | 'screened'
  | 'interviewed'
  | 'offer'
  | 'closed';

export interface ApplicationPipelineProps {
  applicationId: string;
  currentStage: ApplicationStage;
  stageTimestamps?: Partial<Record<ApplicationStage, string>>;
  isActive?: boolean;
  className?: string;
  onStageClick?: (stage: ApplicationStage) => void;
}

interface StageInfo {
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}

const STAGES: Record<ApplicationStage, StageInfo> = {
  applied: {
    label: 'Applied',
    description: 'Submitted your application',
    icon: <FileText className="w-4 h-4" />,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900',
  },
  screened: {
    label: 'Screened',
    description: 'Application under review',
    icon: <FileText className="w-4 h-4" />,
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-100 dark:bg-amber-900',
  },
  interviewed: {
    label: 'Interviewed',
    description: 'Interview scheduled or completed',
    icon: <Users className="w-4 h-4" />,
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-100 dark:bg-purple-900',
  },
  offer: {
    label: 'Offer',
    description: 'Offer extended',
    icon: <Gift className="w-4 h-4" />,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900',
  },
  closed: {
    label: 'Closed',
    description: 'Application closed',
    icon: <X className="w-4 h-4" />,
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-100 dark:bg-red-900',
  },
};

const STAGE_ORDER: ApplicationStage[] = [
  'applied',
  'screened',
  'interviewed',
  'offer',
  'closed',
];

const StageIndicator: React.FC<{
  stage: ApplicationStage;
  isCompleted: boolean;
  isCurrent: boolean;
  isActive: boolean;
  onClick?: () => void;
}> = React.memo(({ stage, isCompleted, isCurrent, isActive, onClick }) => {
  const info = STAGES[stage];

  const isClickable = isActive && isCurrent;

  return (
    <div
      className={`flex flex-col items-center gap-2 ${
        isClickable ? 'cursor-pointer' : ''
      }`}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : -1}
      onKeyDown={(e) => {
        if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
          onClick?.();
        }
      }}
    >
      {/* Icon circle */}
      <div
        className={`relative w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${
          isCompleted
            ? 'bg-green-500 border-green-500'
            : isCurrent
              ? `${info.bgColor} border-2 border-primary`
              : 'border-muted-foreground/30 bg-muted'
        } ${isClickable ? 'hover:shadow-lg' : ''}`}
      >
        {isCompleted ? (
          <CheckCircle2 className="w-5 h-5 text-white" />
        ) : isCurrent ? (
          <div className="absolute inset-0.5 rounded-full border-2 border-current opacity-30 animate-pulse" />
        ) : (
          <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40" />
        )}
        {!isCompleted && !isCurrent && info.icon}
      </div>

      {/* Label */}
      <div className="text-center">
        <p className="text-xs font-semibold">{info.label}</p>
      </div>
    </div>
  );
});

StageIndicator.displayName = 'StageIndicator';

export const ApplicationPipeline: React.FC<ApplicationPipelineProps> = React.memo(
  ({
    applicationId,
    currentStage,
    stageTimestamps = {},
    isActive = true,
    className = '',
    onStageClick,
  }) => {
    const currentStageIndex = useMemo(
      () => STAGE_ORDER.indexOf(currentStage),
      [currentStage]
    );

    const completionPercentage = useMemo(() => {
      const totalStages = STAGE_ORDER.length;
      const completedStages = Math.min(currentStageIndex + 1, totalStages);
      return Math.round((completedStages / totalStages) * 100);
    }, [currentStageIndex]);

    const handleStageClick = useCallback(
      (stage: ApplicationStage) => {
        onStageClick?.(stage);
      },
      [onStageClick]
    );

    return (
      <Card className={`w-full ${className}`}>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Application Pipeline</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Visual pipeline */}
          <div className="flex items-end justify-between gap-2 px-2">
            {STAGE_ORDER.map((stage, index) => {
              const isCompleted = index < currentStageIndex;
              const isCurrent = index === currentStageIndex;

              return (
                <div key={stage} className="flex-1 flex flex-col items-center">
                  <StageIndicator
                    stage={stage}
                    isCompleted={isCompleted}
                    isCurrent={isCurrent}
                    isActive={isActive}
                    onClick={() => handleStageClick(stage)}
                  />

                  {/* Connector line */}
                  {index < STAGE_ORDER.length - 1 && (
                    <div className="h-1 w-full mt-3 bg-muted-foreground/20 relative">
                      {index < currentStageIndex && (
                        <div className="h-full bg-green-500 absolute inset-0" />
                      )}
                      {index === currentStageIndex && (
                        <div
                          className="h-full bg-gradient-to-r from-primary to-muted-foreground/20 absolute inset-0"
                          style={{
                            background:
                              'linear-gradient(to right, var(--color-primary) 0%, var(--color-primary) 50%, var(--color-muted-foreground/0.2) 100%)',
                          }}
                        />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Progress text and current stage info */}
          <div className="space-y-3 pt-2">
            {/* Progress info */}
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-foreground">
                Progress: {completionPercentage}%
              </span>
              <span className="text-muted-foreground text-xs">
                {currentStageIndex + 1} of {STAGE_ORDER.length}
              </span>
            </div>

            {/* Current stage card */}
            <div className={`p-3 rounded-lg border ${STAGES[currentStage].bgColor} border-current/30`}>
              <div className="flex items-start gap-3">
                <div className={`mt-0.5 ${STAGES[currentStage].color}`}>
                  {STAGES[currentStage].icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm">
                    {STAGES[currentStage].label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {STAGES[currentStage].description}
                  </p>
                  {stageTimestamps[currentStage] && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(stageTimestamps[currentStage]!).toLocaleDateString(
                        'en-US',
                        { year: 'numeric', month: 'short', day: 'numeric' }
                      )}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Upcoming stages info */}
            {currentStageIndex < STAGE_ORDER.length - 1 && (
              <div className="text-xs text-muted-foreground p-3 bg-secondary/50 rounded-lg">
                <p className="font-medium mb-1">Next step:</p>
                <p>
                  {STAGES[STAGE_ORDER[currentStageIndex + 1]].label} —{' '}
                  {STAGES[STAGE_ORDER[currentStageIndex + 1]].description.toLowerCase()}
                </p>
              </div>
            )}

            {/* Closed/Completed state */}
            {currentStage === 'closed' && (
              <div className="flex items-start gap-2 p-3 bg-red-100 dark:bg-red-900/30 rounded-lg border border-red-200 dark:border-red-800">
                <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-red-700 dark:text-red-200">
                  This application has been closed.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }
);

ApplicationPipeline.displayName = 'ApplicationPipeline';
