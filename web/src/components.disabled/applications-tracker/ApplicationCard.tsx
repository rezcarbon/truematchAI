'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Calendar,
  Clock,
  MapPin,
  FileText,
  MessageSquare,
  ChevronRight,
  Star,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { HorizontalPipeline } from './types';

export interface ApplicationCardProps {
  application: HorizontalPipeline.Application;
  onViewDetails: (applicationId: string) => void;
  onScheduleInterview: (applicationId: string) => void;
  featured?: boolean;
  compact?: boolean;
}

export function ApplicationCard({
  application,
  onViewDetails,
  onScheduleInterview,
  featured = false,
  compact = false,
}: ApplicationCardProps) {
  const daysSinceApplied = Math.floor(
    (Date.now() - new Date(application.appliedAt).getTime()) / (1000 * 60 * 60 * 24)
  );

  const getScoreColor = (score?: number) => {
    if (!score) return 'text-gray-500';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score?: number) => {
    if (!score) return 'bg-gray-100';
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <Card
      className={cn(
        'transition-all hover:shadow-lg cursor-pointer',
        featured && 'ring-2 ring-blue-500 shadow-lg'
      )}
      onClick={() => onViewDetails(application.id)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base truncate">
              {application.candidateName}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {application.positionTitle}
            </p>
          </div>
          {featured && (
            <Star className="w-5 h-5 text-yellow-500 fill-yellow-500 flex-shrink-0" />
          )}
        </div>

        {/* Status badge and days badge */}
        <div className="flex gap-2 mt-2">
          <Badge variant="outline" className="capitalize">
            {application.status.replace('_', ' ')}
          </Badge>
          <Badge variant="secondary" className="text-xs">
            {daysSinceApplied}d ago
          </Badge>
          {application.isUrgent && (
            <Badge variant="destructive" className="text-xs">
              <AlertCircle className="w-3 h-3 mr-1" />
              Urgent
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className={cn(
        'space-y-3',
        compact && 'space-y-2'
      )}>
        {/* Scores grid */}
        {(application.scores.keyword ||
          application.scores.semantic ||
          application.scores.capability) && (
          <div className="grid grid-cols-3 gap-2">
            {application.scores.keyword && (
              <div className={cn('rounded p-2 text-center', getScoreBgColor(application.scores.keyword))}>
                <p className="text-xs font-medium text-gray-600">Keyword</p>
                <p className={cn('text-lg font-bold', getScoreColor(application.scores.keyword))}>
                  {application.scores.keyword}%
                </p>
              </div>
            )}
            {application.scores.semantic && (
              <div className={cn('rounded p-2 text-center', getScoreBgColor(application.scores.semantic))}>
                <p className="text-xs font-medium text-gray-600">Semantic</p>
                <p className={cn('text-lg font-bold', getScoreColor(application.scores.semantic))}>
                  {application.scores.semantic}%
                </p>
              </div>
            )}
            {application.scores.capability && (
              <div className={cn('rounded p-2 text-center', getScoreBgColor(application.scores.capability))}>
                <p className="text-xs font-medium text-gray-600">Capability</p>
                <p className={cn('text-lg font-bold', getScoreColor(application.scores.capability))}>
                  {application.scores.capability}%
                </p>
              </div>
            )}
          </div>
        )}

        {/* Application details */}
        <div className="space-y-2 text-sm">
          {application.location && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <MapPin className="w-4 h-4 flex-shrink-0" />
              <span>{application.location}</span>
            </div>
          )}

          {application.appliedAt && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Calendar className="w-4 h-4 flex-shrink-0" />
              <span>{new Date(application.appliedAt).toLocaleDateString()}</span>
            </div>
          )}

          {application.lastInterviewDate && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock className="w-4 h-4 flex-shrink-0" />
              <span>Interview: {new Date(application.lastInterviewDate).toLocaleDateString()}</span>
            </div>
          )}
        </div>

        {/* Tags */}
        {application.tags && application.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {application.tags.slice(0, 2).map(tag => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
            {application.tags.length > 2 && (
              <Badge variant="secondary" className="text-xs">
                +{application.tags.length - 2}
              </Badge>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2 pt-2 border-t">
          <Button
            size="sm"
            variant="ghost"
            className="flex-1 h-8 text-xs"
            onClick={e => {
              e.stopPropagation();
              onViewDetails(application.id);
            }}
          >
            <FileText className="w-3 h-3 mr-1" />
            Details
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="flex-1 h-8 text-xs"
            onClick={e => {
              e.stopPropagation();
              onScheduleInterview(application.id);
            }}
          >
            <MessageSquare className="w-3 h-3 mr-1" />
            Interview
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0"
            onClick={e => {
              e.stopPropagation();
              onViewDetails(application.id);
            }}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
