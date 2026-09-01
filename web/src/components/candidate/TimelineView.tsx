'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle2,
  FileText,
  Users,
  Gift,
  MessageSquare,
  AlertCircle,
  Clock,
  User,
} from 'lucide-react';

export type TimelineEventType =
  | 'applied'
  | 'screened'
  | 'interviewed'
  | 'offer'
  | 'feedback'
  | 'update'
  | 'rejection'
  | 'other';

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description?: string;
  timestamp: string;
  actor?: {
    name: string;
    role?: string;
    avatar?: string;
  };
  details?: Record<string, unknown>;
}

export interface TimelineViewProps {
  events: TimelineEvent[];
  title?: string;
  className?: string;
}

const EVENT_ICONS: Record<TimelineEventType, React.ReactNode> = {
  applied: <FileText className="w-4 h-4" />,
  screened: <FileText className="w-4 h-4" />,
  interviewed: <Users className="w-4 h-4" />,
  offer: <Gift className="w-4 h-4" />,
  feedback: <MessageSquare className="w-4 h-4" />,
  update: <AlertCircle className="w-4 h-4" />,
  rejection: <AlertCircle className="w-4 h-4" />,
  other: <Clock className="w-4 h-4" />,
};

const EVENT_COLORS: Record<TimelineEventType, string> = {
  applied: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
  screened: 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200',
  interviewed: 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200',
  offer: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
  feedback: 'bg-cyan-100 dark:bg-cyan-900 text-cyan-800 dark:text-cyan-200',
  update: 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200',
  rejection: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
  other: 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200',
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const formatTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
};

const TimelineEventCard: React.FC<{
  event: TimelineEvent;
  isFirst: boolean;
  isLast: boolean;
}> = React.memo(({ event, isFirst, isLast }) => {
  const eventDate = new Date(event.timestamp);
  const displayDate = formatDate(event.timestamp);
  const displayTime = formatTime(event.timestamp);

  return (
    <div className="relative">
      {/* Connector line */}
      {!isLast && (
        <div className="absolute left-5 top-14 h-12 w-0.5 bg-muted-foreground/20" />
      )}

      {/* Event container */}
      <div className="flex gap-4">
        {/* Timeline dot */}
        <div className="flex flex-col items-center pt-1 flex-shrink-0">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center border-2 border-background ${EVENT_COLORS[event.type]}`}
          >
            {event.type === 'offer' ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : (
              EVENT_ICONS[event.type]
            )}
          </div>
        </div>

        {/* Event content */}
        <div className="flex-1 pb-8 min-w-0">
          <div className="space-y-2">
            {/* Header with title and badge */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <h3 className="font-semibold text-base">{event.title}</h3>
              </div>
              <Badge
                variant="secondary"
                className={`whitespace-nowrap text-xs font-medium ${EVENT_COLORS[event.type]}`}
              >
                {event.type.charAt(0).toUpperCase() + event.type.slice(1)}
              </Badge>
            </div>

            {/* Description if available */}
            {event.description && (
              <p className="text-sm text-muted-foreground">{event.description}</p>
            )}

            {/* Date and time */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
              <span>{displayDate}</span>
              <span>{displayTime}</span>
            </div>

            {/* Actor information */}
            {event.actor && (
              <div className="flex items-center gap-2 mt-2 p-2 bg-secondary/50 rounded-lg">
                {event.actor.avatar ? (
                  <img
                    src={event.actor.avatar}
                    alt={event.actor.name}
                    className="w-6 h-6 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center">
                    <User className="w-3 h-3 text-muted-foreground" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate">
                    {event.actor.name}
                  </p>
                  {event.actor.role && (
                    <p className="text-xs text-muted-foreground">{event.actor.role}</p>
                  )}
                </div>
              </div>
            )}

            {/* Additional details if available */}
            {event.details && Object.keys(event.details).length > 0 && (
              <div className="mt-3 space-y-2 p-3 bg-secondary/30 rounded-lg">
                {Object.entries(event.details).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-start gap-2">
                    <span className="text-xs font-medium text-muted-foreground capitalize">
                      {key.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-xs text-foreground text-right max-w-xs truncate">
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

TimelineEventCard.displayName = 'TimelineEventCard';

export const TimelineView: React.FC<TimelineViewProps> = React.memo(
  ({ events, title = 'Application Timeline', className = '' }) => {
    const sortedEvents = useMemo(() => {
      // Sort events by timestamp in descending order (newest first)
      return [...events].sort(
        (a, b) =>
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
    }, [events]);

    if (sortedEvents.length === 0) {
      return (
        <Card className={className}>
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Clock className="w-12 h-12 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">
                No events recorded yet
              </p>
            </div>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            {sortedEvents.length} event{sortedEvents.length !== 1 ? 's' : ''}
          </p>
        </CardHeader>

        <CardContent>
          <div className="space-y-0">
            {sortedEvents.map((event, index) => (
              <TimelineEventCard
                key={event.id}
                event={event}
                isFirst={index === 0}
                isLast={index === sortedEvents.length - 1}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }
);

TimelineView.displayName = 'TimelineView';
