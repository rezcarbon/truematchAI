'use client';

/**
 * Job card component displaying job info with match score
 */

import React, { useState } from 'react';
import { Heart, MapPin, DollarSign, Briefcase, ChevronRight } from 'lucide-react';
import { MatchScoreDisplay } from './MatchScoreDisplay';
import { HiddenGemBadge } from './HiddenGemBadge';
import type { JobWithCapabilityMatch } from '@/types/jobs';

interface JobCardProps {
  job: JobWithCapabilityMatch;
  onOpenDetails: (job: JobWithCapabilityMatch) => void;
  onOpenApply: (job: JobWithCapabilityMatch) => void;
  isSaved?: boolean;
  onToggleSave?: (jobId: string) => Promise<void>;
}

export function JobCard({
  job,
  onOpenDetails,
  onOpenApply,
  isSaved = false,
  onToggleSave,
}: JobCardProps) {
  const [isSavingLoading, setIsSavingLoading] = useState(false);

  const handleSave = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!onToggleSave) return;

    try {
      setIsSavingLoading(true);
      await onToggleSave(job.id);
    } finally {
      setIsSavingLoading(false);
    }
  };

  const topSkills = job.skillsAlignment.matchedSkills
    .sort((a, b) => b.match - a.match)
    .slice(0, 3);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
      {/* Header with match score */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-bold text-gray-900 text-lg">{job.title}</h3>
            {job.isHiddenGem && (
              <HiddenGemBadge reason={job.hiddenGemReason} size="sm" />
            )}
          </div>
          <p className="text-sm text-gray-600">{job.company}</p>
        </div>

        <div className="flex flex-col items-center gap-2">
          <MatchScoreDisplay score={job.capabilityMatch.score} size="md" />
          <button
            onClick={handleSave}
            disabled={isSavingLoading}
            className="p-2 hover:bg-gray-100 rounded-lg transition disabled:opacity-50"
          >
            <Heart
              className="w-5 h-5"
              fill={isSaved ? '#ef4444' : 'none'}
              stroke={isSaved ? '#ef4444' : '#9ca3af'}
            />
          </button>
        </div>
      </div>

      {/* Job details row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-sm">
        <div className="flex items-center gap-1 text-gray-600">
          <MapPin className="w-4 h-4" />
          <span>{job.location}</span>
        </div>
        <div className="flex items-center gap-1 text-gray-600">
          <DollarSign className="w-4 h-4" />
          <span>${job.salaryMin.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-1 text-gray-600">
          <Briefcase className="w-4 h-4" />
          <span className="capitalize">{job.remote}</span>
        </div>
        <div className="text-gray-600">
          <span className="capitalize">{job.level}</span>
        </div>
      </div>

      {/* Top skills */}
      {topSkills.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold text-gray-700 mb-2">Top Skills Match</p>
          <div className="flex flex-wrap gap-2">
            {topSkills.map((skill) => (
              <div
                key={skill.name}
                className="px-2 py-1 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700 font-medium"
              >
                {skill.name}
                <span className="ml-1 text-blue-600">({skill.match}%)</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing skills warning */}
      {job.skillsAlignment.missingSkills.length > 0 && (
        <div className="mb-4 p-2 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs font-semibold text-amber-900">
            Missing: {job.skillsAlignment.missingSkills
              .slice(0, 2)
              .map((s) => s.name)
              .join(', ')}
            {job.skillsAlignment.missingSkills.length > 2 && ' +more'}
          </p>
        </div>
      )}

      {/* Match reasoning */}
      <div className="mb-4 p-2 bg-gray-50 rounded-lg">
        <p className="text-xs text-gray-700">
          {job.capabilityMatch.reasoning[0]}
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onOpenDetails(job)}
          className="flex-1 px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium text-sm transition flex items-center justify-center gap-1"
        >
          Details
          <ChevronRight className="w-4 h-4" />
        </button>
        <button
          onClick={() => onOpenApply(job)}
          className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm transition"
        >
          Apply Now
        </button>
      </div>
    </div>
  );
}
