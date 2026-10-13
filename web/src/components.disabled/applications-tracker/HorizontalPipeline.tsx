'use client';

import React from 'react';
import { ChevronRight, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface PipelineStage {
  id: string;
  label: string;
  color: string;
  icon?: React.ReactNode;
}

export interface ApplicationStatus {
  applicationId: string;
  currentStage: string;
  completedStages: string[];
  timestamp: Date;
}

const PIPELINE_STAGES: PipelineStage[] = [
  { id: 'applied', label: 'Applied', color: 'bg-blue-500' },
  { id: 'screened', label: 'Screened', color: 'bg-purple-500' },
  { id: 'interviewed', label: 'Interviewed', color: 'bg-indigo-500' },
  { id: 'offer', label: 'Offer', color: 'bg-yellow-500' },
  { id: 'closed', label: 'Closed', color: 'bg-green-500' },
];

interface HorizontalPipelineProps {
  applicationStatus: ApplicationStatus;
  onStageClick?: (stageId: string) => void;
  compact?: boolean;
}

export function HorizontalPipeline({
  applicationStatus,
  onStageClick,
  compact = false,
}: HorizontalPipelineProps) {
  const currentStageIndex = PIPELINE_STAGES.findIndex(
    s => s.id === applicationStatus.currentStage
  );

  const isStageCompleted = (stageId: string) =>
    applicationStatus.completedStages.includes(stageId);
  const isStageCurrent = (stageId: string) =>
    stageId === applicationStatus.currentStage;

  return (
    <div className={cn(
      'w-full',
      compact ? 'py-2' : 'py-4'
    )}>
      <div className="flex items-center justify-between gap-2">
        {PIPELINE_STAGES.map((stage, index) => {
          const isCompleted = isStageCompleted(stage.id);
          const isCurrent = isStageCurrent(stage.id);
          const isAfterCurrent = index > currentStageIndex && !isCompleted;

          return (
            <React.Fragment key={stage.id}>
              {/* Stage dot and label */}
              <button
                onClick={() => onStageClick?.(stage.id)}
                className={cn(
                  'flex flex-col items-center gap-1 cursor-pointer transition-all',
                  'hover:scale-110',
                  onStageClick ? 'hover:opacity-80' : 'cursor-default'
                )}
              >
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center transition-all',
                    isCompleted && 'ring-2 ring-offset-2 ring-green-500',
                    isCurrent && `${stage.color} ring-2 ring-offset-2 ring-current`,
                    !isCompleted && !isCurrent && 'bg-gray-300',
                    isCompleted ? 'bg-green-500' : stage.color,
                    isAfterCurrent && 'opacity-50'
                  )}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5 text-white" />
                  ) : isCurrent ? (
                    <Clock className="w-5 h-5 text-white animate-pulse" />
                  ) : (
                    <span className="text-xs font-bold text-white">
                      {index + 1}
                    </span>
                  )}
                </div>
                {!compact && (
                  <span
                    className={cn(
                      'text-xs font-medium whitespace-nowrap',
                      isCompleted && 'text-green-600',
                      isCurrent && 'text-blue-600 font-bold',
                      !isCompleted && !isCurrent && 'text-gray-500'
                    )}
                  >
                    {stage.label}
                  </span>
                )}
              </button>

              {/* Connector arrow */}
              {index < PIPELINE_STAGES.length - 1 && (
                <div
                  className={cn(
                    'flex-1 h-1 rounded-full transition-colors',
                    isCompleted ? 'bg-green-500' : 'bg-gray-300'
                  )}
                >
                  <ChevronRight
                    className={cn(
                      'w-4 h-4 float-right -mr-2 -mt-1.5',
                      isCompleted ? 'text-green-500' : 'text-gray-300'
                    )}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Progress percentage */}
      <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{
              width: `${((currentStageIndex + 1) / PIPELINE_STAGES.length) * 100}%`,
            }}
          />
        </div>
        <span className="font-medium">
          {Math.round(((currentStageIndex + 1) / PIPELINE_STAGES.length) * 100)}%
        </span>
      </div>
    </div>
  );
}
