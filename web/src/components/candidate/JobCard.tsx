'use client';

import { Job, CapabilityMatch } from '@/types/jobs';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  MapPin,
  Building2,
  DollarSign,
  Briefcase,
  Star,
  ArrowRight,
  Zap,
} from 'lucide-react';
import Link from 'next/link';

interface JobCardProps {
  job: Job & { capabilityMatch?: CapabilityMatch };
  onApply?: (jobId: string) => void;
  isLoading?: boolean;
}

export function JobCard({ job, onApply, isLoading = false }: JobCardProps) {
  const matchScore = job.capabilityMatch?.score ?? 0;
  const matchType = job.capabilityMatch?.matchType ?? 'partial';
  const isHiddenGem = job.isHiddenGem ?? false;

  const getMatchColor = (score: number) => {
    if (score >= 80) return { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' };
    if (score >= 60) return { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' };
    if (score >= 40) return { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' };
    return { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' };
  };

  const getMatchLabel = (type: string) => {
    switch (type) {
      case 'exact':
        return 'Perfect Match';
      case 'strong':
        return 'Strong Match';
      case 'partial':
        return 'Possible Match';
      case 'hidden_gem':
        return 'Hidden Gem';
      default:
        return 'Match';
    }
  };

  const matchColorClass = getMatchColor(matchScore);
  const salaryDisplay = `${job.salaryMin?.toLocaleString() ?? 'N/A'} - ${job.salaryMax?.toLocaleString() ?? 'N/A'}`;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <Link href={`/candidate/jobs/${job.id}`} className="group">
              <h3 className="font-semibold text-base group-hover:text-primary transition-colors truncate">
                {job.title}
              </h3>
            </Link>
            <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
              <Building2 className="h-4 w-4" />
              {job.company}
            </p>
          </div>

          {/* Match Score Badge */}
          <div
            className={`flex-shrink-0 flex flex-col items-center justify-center rounded-lg p-2 ${matchColorClass.bg} border ${matchColorClass.border}`}
          >
            <div className={`text-lg font-bold ${matchColorClass.text}`}>
              {Math.round(matchScore)}%
            </div>
            <div className={`text-xs font-medium ${matchColorClass.text}`}>
              {getMatchLabel(matchType)}
            </div>
          </div>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-2 mt-3">
          {isHiddenGem && (
            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
              <Zap className="h-3 w-3 mr-1" />
              Hidden Gem
            </Badge>
          )}
          <Badge variant="outline" className="text-xs">
            {job.level}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {job.jobType}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Location and Remote */}
        <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <MapPin className="h-4 w-4" />
            {job.location}
          </span>
          <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-muted text-xs">
            {job.remote === 'fully'
              ? '🏠 Fully Remote'
              : job.remote === 'hybrid'
              ? '🔄 Hybrid'
              : '🏢 On-site'}
          </span>
        </div>

        {/* Salary */}
        {job.salaryMin && job.salaryMax && (
          <div className="flex items-center gap-2 text-sm">
            <DollarSign className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">{salaryDisplay}</span>
            {job.salary_currency && (
              <span className="text-xs text-muted-foreground">{job.salary_currency}</span>
            )}
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-2 text-xs bg-muted/50 rounded-lg p-2">
          <div>
            <p className="text-muted-foreground">Experience</p>
            <p className="font-medium">
              {job.yearsOfExperienceRequired} year{job.yearsOfExperienceRequired !== 1 ? 's' : ''}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Industry</p>
            <p className="font-medium truncate">{job.industry}</p>
          </div>
        </div>

        {/* Match Reasoning */}
        {job.capabilityMatch?.reasoning && job.capabilityMatch.reasoning.length > 0 && (
          <div className="bg-blue-50/50 border border-blue-200/50 rounded p-2">
            <p className="text-xs text-blue-900">
              <span className="font-semibold">Why it matches:</span> {job.capabilityMatch.reasoning[0]}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Link href={`/candidate/jobs/${job.id}`} className="flex-1">
            <Button variant="outline" size="sm" className="w-full">
              View Details
              <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </Link>
          <Button
            size="sm"
            onClick={() => onApply?.(job.id)}
            disabled={isLoading}
            className="flex-1"
          >
            {isLoading ? (
              <>
                <span className="inline-block w-4 h-4 animate-spin mr-1">⏳</span>
                Applying...
              </>
            ) : (
              <>
                <Star className="h-3 w-3 mr-1" />
                Apply
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
