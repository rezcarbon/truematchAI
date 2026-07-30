'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface TimelineEvent {
  id: string;
  status: 'profile_sent' | 'profile_viewed' | 'interview_scheduled' | 'interview_completed' | 'offer_received' | 'rejected';
  message: string;
  timestamp: Date;
  emailSent?: boolean;
}

interface MatchTimelineProps {
  events?: TimelineEvent[];
  companyName?: string;
}

const STATUS_CONFIG = {
  profile_sent: {
    icon: '📤',
    label: 'Profile Sent',
    color: 'text-blue-600',
  },
  profile_viewed: {
    icon: '👁️',
    label: 'Profile Viewed',
    color: 'text-green-600',
  },
  interview_scheduled: {
    icon: '📅',
    label: 'Interview Scheduled',
    color: 'text-purple-600',
  },
  interview_completed: {
    icon: '✅',
    label: 'Interview Completed',
    color: 'text-blue-600',
  },
  offer_received: {
    icon: '🎉',
    label: 'Offer Received',
    color: 'text-green-700',
  },
  rejected: {
    icon: '📋',
    label: 'Position Filled',
    color: 'text-gray-500',
  },
};

export function MatchTimeline({ events = [], companyName = 'Recruiter' }: MatchTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <Card className="bg-muted/30">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            Waiting for updates from {companyName}...
          </div>
        </CardContent>
      </Card>
    );
  }

  // Sort events by timestamp (newest first)
  const sortedEvents = [...events].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Match Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {sortedEvents.map((event, index) => {
            const config = STATUS_CONFIG[event.status];
            const isLatest = index === 0;

            return (
              <div key={event.id} className="flex gap-3">
                {/* Timeline dot */}
                <div className="flex flex-col items-center">
                  <div className={`text-lg ${isLatest ? 'animate-pulse' : ''}`}>
                    {config.icon}
                  </div>
                  {index < sortedEvents.length - 1 && (
                    <div className="w-0.5 h-8 bg-gray-300 my-1" />
                  )}
                </div>

                {/* Event details */}
                <div className="flex-1 pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className={`font-medium text-sm ${config.color}`}>
                        {config.label}
                      </p>
                      {event.message && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {event.message}
                        </p>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                      {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                    </span>
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
