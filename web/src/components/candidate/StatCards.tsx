'use client';

import React, { useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowUp, ArrowDown, TrendingUp, CheckCircle2, Briefcase, MessageSquare } from 'lucide-react';

export interface StatCardData {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
  };
  description?: string;
  suffix?: string;
  color?: 'blue' | 'green' | 'purple' | 'amber';
}

export interface StatCardsProps {
  stats: StatCardData[];
  className?: string;
}

const STAT_COLORS = {
  blue: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-600 dark:text-blue-400',
  },
  green: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    text: 'text-green-600 dark:text-green-400',
  },
  purple: {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-600 dark:text-purple-400',
  },
  amber: {
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    text: 'text-amber-600 dark:text-amber-400',
  },
};

const StatCard: React.FC<{ stat: StatCardData }> = React.memo(({ stat }) => {
  const colors = useMemo(
    () => STAT_COLORS[stat.color || 'blue'],
    [stat.color]
  );

  const TrendIcon = useMemo(() => {
    if (!stat.trend) return null;
    if (stat.trend.direction === 'up') return ArrowUp;
    if (stat.trend.direction === 'down') return ArrowDown;
    return null;
  }, [stat.trend]);

  const trendColor = useMemo(() => {
    if (!stat.trend) return 'text-muted-foreground';
    if (stat.trend.direction === 'up') return 'text-green-600 dark:text-green-400';
    if (stat.trend.direction === 'down') return 'text-red-600 dark:text-red-400';
    return 'text-muted-foreground';
  }, [stat.trend?.direction]);

  return (
    <Card className="overflow-hidden hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          {/* Icon */}
          <div className={`p-3 rounded-lg ${colors.bg} flex-shrink-0`}>
            <div className={colors.text}>{stat.icon}</div>
          </div>

          {/* Trend indicator */}
          {stat.trend && TrendIcon && (
            <div className={`flex items-center gap-1 text-sm font-medium ${trendColor}`}>
              <TrendIcon className="w-4 h-4" />
              <span>{Math.abs(stat.trend.value)}%</span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="mt-4">
          <p className="text-sm text-muted-foreground mb-1">{stat.label}</p>
          <div className="flex items-baseline gap-1">
            <p className="text-3xl font-bold text-foreground">
              {stat.value}
            </p>
            {stat.suffix && (
              <span className="text-sm text-muted-foreground">{stat.suffix}</span>
            )}
          </div>
          {stat.description && (
            <p className="text-xs text-muted-foreground mt-2">{stat.description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
});

StatCard.displayName = 'StatCard';

export const StatCards: React.FC<StatCardsProps> = React.memo(
  ({ stats, className = '' }) => {
    // Default stats if not provided - used for demo/scaffolding
    const displayStats = useMemo(() => {
      if (stats.length > 0) return stats;

      return [
        {
          label: 'Assessments Completed',
          value: 5,
          icon: <CheckCircle2 className="w-6 h-6" />,
          trend: { value: 20, direction: 'up' as const },
          description: 'In the last 30 days',
          color: 'blue' as const,
        },
        {
          label: 'Average Score',
          value: 76,
          icon: <TrendingUp className="w-6 h-6" />,
          trend: { value: 5, direction: 'up' as const },
          description: 'Across all assessments',
          suffix: '%',
          color: 'green' as const,
        },
        {
          label: 'Active Applications',
          value: 12,
          icon: <Briefcase className="w-6 h-6" />,
          trend: { value: 8, direction: 'up' as const },
          description: 'Pending or in progress',
          color: 'purple' as const,
        },
        {
          label: 'Interviews Scheduled',
          value: 3,
          icon: <MessageSquare className="w-6 h-6" />,
          trend: { value: 2, direction: 'down' as const },
          description: 'Upcoming interviews',
          color: 'amber' as const,
        },
      ];
    }, [stats]);

    return (
      <div
        className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 ${className}`}
      >
        {displayStats.map((stat, index) => (
          <StatCard key={index} stat={stat} />
        ))}
      </div>
    );
  }
);

StatCards.displayName = 'StatCards';
