'use client';

import React, { useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Briefcase,
  Building2,
  Calendar,
  Eye,
  TrendingUp,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import type { ApplicationStage } from './ApplicationPipeline';

export interface ApplicationCardProps {
  id: string;
  jobTitle: string;
  company: string;
  stage: ApplicationStage;
  appliedDate: string;
  stageDate?: string;
  logo?: string;
  matchScore?: number;
  location?: string;
  onViewDetails: (id: string) => void;
  onTrackStatus?: (id: string) => void;
  className?: string;
}

const STAGE_BADGE_VARIANTS: Record<ApplicationStage, { color: string; label: string }> = {
  applied: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200', label: 'Applied' },
  screened: { color: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200', label: 'Screened' },
  interviewed: { color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200', label: 'Interviewed' },
  offer: { color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200', label: 'Offer' },
  closed: { color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', label: 'Closed' },
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const ApplicationCard: React.FC<ApplicationCardProps> = React.memo(
  ({
    id,
    jobTitle,
    company,
    stage,
    appliedDate,
    stageDate,
    logo,
    matchScore,
    location,
    onViewDetails,
    onTrackStatus,
    className = '',
  }) => {
    const stageBadge = useMemo(() => STAGE_BADGE_VARIANTS[stage], [stage]);

    const daysSinceApplied = useMemo(() => {
      const now = new Date();
      const applied = new Date(appliedDate);
      const diff = Math.floor((now.getTime() - applied.getTime()) / (1000 * 60 * 60 * 24));
      return diff;
    }, [appliedDate]);

    const handleViewDetails = useCallback(() => {
      onViewDetails(id);
    }, [id, onViewDetails]);

    const handleTrackStatus = useCallback(() => {
      onTrackStatus?.(id);
    }, [id, onTrackStatus]);

    return (
      <Card className={`overflow-hidden hover:shadow-lg transition-shadow ${className}`}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              {/* Company and logo */}
              <div className="flex items-center gap-3 mb-2">
                {logo && (
                  <img
                    src={logo}
                    alt={company}
                    className="w-8 h-8 rounded object-cover bg-muted"
                  />
                )}
                <div>
                  <p className="text-xs font-medium text-muted-foreground">
                    {company}
                  </p>
                </div>
              </div>

              {/* Job title */}
              <CardTitle className="text-lg truncate">{jobTitle}</CardTitle>

              {/* Location if available */}
              {location && (
                <p className="text-xs text-muted-foreground mt-1">{location}</p>
              )}
            </div>

            {/* Stage badge */}
            <Badge
              variant="secondary"
              className={`whitespace-nowrap ${stageBadge.color} font-medium`}
            >
              {stageBadge.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Meta info grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-start gap-2">
              <Calendar className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-muted-foreground">Applied</p>
                <p className="text-sm font-medium">{formatDate(appliedDate)}</p>
                <p className="text-xs text-muted-foreground">{daysSinceApplied}d ago</p>
              </div>
            </div>

            {stageDate && (
              <div className="flex items-start gap-2">
                <TrendingUp className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs text-muted-foreground">
                    {stageBadge.label}
                  </p>
                  <p className="text-sm font-medium">{formatDate(stageDate)}</p>
                </div>
              </div>
            )}
          </div>

          {/* Match score if available */}
          {matchScore !== undefined && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Match Score</span>
                </div>
                <span className="text-sm font-semibold">{matchScore}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    matchScore >= 80
                      ? 'bg-green-500'
                      : matchScore >= 60
                        ? 'bg-amber-500'
                        : 'bg-red-500'
                  }`}
                  style={{ width: `${matchScore}%` }}
                />
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={handleViewDetails}
            >
              <Eye className="w-4 h-4 mr-2" />
              View Details
            </Button>

            {stage !== 'closed' && (
              <Button
                variant="ghost"
                size="sm"
                className="px-3"
                onClick={handleTrackStatus}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }
);

ApplicationCard.displayName = 'ApplicationCard';
