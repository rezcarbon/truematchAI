'use client';

import React from 'react';
import {
  ArrowRight,
  MessageSquare,
  Zap,
  CheckCircle2,
  Calendar,
  FileText,
  Phone,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import type { HorizontalPipeline as Pipeline } from './types';

interface TimelineViewProps {
  events: Pipeline.TimelineEvent[];
  compact?: boolean;
}

const eventTypeConfig = {
  status_change: {
    icon: ArrowRight,
    label: 'Status Changed',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
  interview: {
    icon: MessageSquare,
    label: 'Interview',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
  },
  feedback: {
    icon: Zap,
    label: 'Feedback',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
  },
  offer: {
    icon: CheckCircle2,
    label: 'Offer',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
  note: {
    icon: FileText,
    label: 'Note',
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
  },
  call: {
    icon: Phone,
    label: 'Call',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
  },
};

export function TimelineView({ events, compact = false }: TimelineViewProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        No events yet
      </div>
    );
  }

  const sortedEvents = [...events].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return (
    <div className={cn('space-y-4', compact && 'space-y-2')}>
      {sortedEvents.map((event, index) => {
        const config = eventTypeConfig[event.type] || eventTypeConfig.note;
        const Icon = config.icon;

        return (
          <div key={event.id} className="flex gap-4">
            {/* Timeline connector */}
            <div className="flex flex-col items-center">
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                config.bgColor
              )}>
                <Icon className={cn('w-4 h-4', config.color)} />
              </div>
              {index < sortedEvents.length - 1 && (
                <div className="w-0.5 h-12 bg-gray-200 my-1" />
              )}
            </div>

            {/* Event content */}
            <div className={cn(
              'pb-4',
              compact ? 'py-0' : 'py-1'
            )}>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  {config.label}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {new Date(event.timestamp).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>

              <p className={cn(
                'font-medium mt-1',
                compact ? 'text-sm' : 'text-base'
              )}>
                {event.title}
              </p>

              {event.description && (
                <p className={cn(
                  'text-muted-foreground mt-1',
                  compact ? 'text-xs' : 'text-sm'
                )}>
                  {event.description}
                </p>
              )}

              {event.metadata && (
                <div className="mt-2 space-y-1">
                  {Object.entries(event.metadata).map(([key, value]) => (
                    value && (
                      <div key={key} className="text-xs text-muted-foreground">
                        <span className="font-medium">{key}:</span> {String(value)}
                      </div>
                    )
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
