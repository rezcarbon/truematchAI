'use client';

import React, { useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  FileText,
  Briefcase,
  MessageSquare,
  Bell,
  Award,
  Send,
  CheckCircle2,
  AlertCircle,
  Calendar,
  ArrowRight,
} from 'lucide-react';

export type ActivityType =
  | 'assessment'
  | 'application'
  | 'message'
  | 'interview'
  | 'offer'
  | 'update'
  | 'notification'
  | 'other';

export interface ActivityFeedItem {
  id: string;
  type: ActivityType;
  title: string;
  description?: string;
  timestamp: string;
  actor?: {
    name: string;
    avatar?: string;
  };
  actionLabel?: string;
  onAction?: () => void;
}

export interface ActivityFeedProps {
  items: ActivityFeedItem[];
  title?: string;
  className?: string;
  maxItems?: number;
  onViewAll?: () => void;
}

const ACTIVITY_ICONS: Record<ActivityType, React.ReactNode> = {
  assessment: <Award className="w-5 h-5" />,
  application: <Briefcase className="w-5 h-5" />,
  message: <MessageSquare className="w-5 h-5" />,
  interview: <Calendar className="w-5 h-5" />,
  offer: <CheckCircle2 className="w-5 h-5" />,
  update: <Bell className="w-5 h-5" />,
  notification: <AlertCircle className="w-5 h-5" />,
  other: <FileText className="w-5 h-5" />,
};

const ACTIVITY_COLORS: Record<ActivityType, string> = {
  assessment: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200',
  application: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200',
  message: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900 dark:text-cyan-200',
  interview: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-200',
  offer: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200',
  update: 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-200',
  notification: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200',
  other: 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-200',
};

const formatTime = (timestamp: string): string => {
  const now = new Date();
  const time = new Date(timestamp);
  const diffMs = now.getTime() - time.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return time.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
};

const ActivityItem: React.FC<{
  item: ActivityFeedItem;
}> = React.memo(({ item }) => {
  const handleAction = useCallback(() => {
    item.onAction?.();
  }, [item]);

  return (
    <div className="flex gap-4 py-4 border-b last:border-b-0">
      {/* Avatar and icon */}
      <div className="flex-shrink-0">
        {item.actor?.avatar ? (
          <img
            src={item.actor.avatar}
            alt={item.actor.name}
            className="w-10 h-10 rounded-full object-cover"
          />
        ) : (
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center ${ACTIVITY_COLORS[item.type]}`}
          >
            {ACTIVITY_ICONS[item.type]}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="font-semibold text-sm text-foreground">
                {item.title}
              </p>
              <Badge
                variant="outline"
                className={`text-xs font-medium ${ACTIVITY_COLORS[item.type]}`}
              >
                {item.type.charAt(0).toUpperCase() + item.type.slice(1)}
              </Badge>
            </div>

            {item.description && (
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                {item.description}
              </p>
            )}

            <div className="flex items-center gap-3 mt-2">
              <span className="text-xs text-muted-foreground">
                {formatTime(item.timestamp)}
              </span>

              {item.actor && (
                <span className="text-xs text-muted-foreground">
                  by {item.actor.name}
                </span>
              )}
            </div>
          </div>

          {/* Action button */}
          {item.actionLabel && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleAction}
              className="text-xs h-8 px-2 flex-shrink-0"
            >
              {item.actionLabel}
              <ArrowRight className="w-3 h-3 ml-1" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
});

ActivityItem.displayName = 'ActivityItem';

export const ActivityFeed: React.FC<ActivityFeedProps> = React.memo(
  ({
    items,
    title = 'Recent Activity',
    className = '',
    maxItems = 5,
    onViewAll,
  }) => {
    const displayItems = useMemo(() => {
      return items.slice(0, maxItems);
    }, [items, maxItems]);

    const hasMore = useMemo(() => {
      return items.length > maxItems;
    }, [items, maxItems]);

    if (items.length === 0) {
      return (
        <Card className={className}>
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Bell className="w-12 h-12 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">
                No recent activity
              </p>
            </div>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle>{title}</CardTitle>
            <Badge variant="secondary" className="text-xs">
              {items.length} new
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-0">
          {displayItems.map((item) => (
            <ActivityItem key={item.id} item={item} />
          ))}

          {hasMore && (
            <div className="py-3 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={onViewAll}
                className="w-full text-xs"
              >
                View all activity
                <ArrowRight className="w-3 h-3 ml-2" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }
);

ActivityFeed.displayName = 'ActivityFeed';
