'use client';

/**
 * Job details modal with full job information and skills alignment
 */

import React from 'react';
import { X, Heart, MapPin, DollarSign, Briefcase, Building2, CalendarDays } from 'lucide-react';
import { SkillsRadarChart } from './SkillsRadarChart';
import { MatchScoreDisplay } from './MatchScoreDisplay';
import { HiddenGemBadge } from './HiddenGemBadge';
import type { JobWithCapabilityMatch } from '@/types/jobs';

interface JobDetailsModalProps {
  job: JobWithCapabilityMatch;
  isOpen: boolean;
  onClose: () => void;
  onApply: () => void;
  isSaved?: boolean;
  onToggleSave?: (jobId: string) => Promise<void>;
}

export function JobDetailsModal({
  job,
  isOpen,
  onClose,
  onApply,
  isSaved = false,
  onToggleSave,
}: JobDetailsModalProps) {
  const [isSavingLoading, setIsSavingLoading] = React.useState(false);

  if (!isOpen) return null;

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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="font-bold text-2xl text-gray-900">{job.title}</h2>
              {job.isHiddenGem && (
                <HiddenGemBadge reason={job.hiddenGemReason} size="md" />
              )}
            </div>
            <p className="text-gray-600">{job.company}</p>
          </div>

          <div className="flex items-center gap-4">
            <MatchScoreDisplay score={job.capabilityMatch.score} size="lg" />
            <button
              onClick={handleSave}
              disabled={isSavingLoading}
              className="p-2 hover:bg-gray-100 rounded-lg transition disabled:opacity-50"
            >
              <Heart
                className="w-6 h-6"
                fill={isSaved ? '#ef4444' : 'none'}
                stroke={isSaved ? '#ef4444' : '#9ca3af'}
              />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Key Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <MapPin className="w-4 h-4" />
                <span className="text-sm font-medium">Location</span>
              </div>
              <p className="font-semibold text-gray-900">{job.location}</p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <DollarSign className="w-4 h-4" />
                <span className="text-sm font-medium">Salary</span>
              </div>
              <p className="font-semibold text-gray-900">
                ${job.salaryMin.toLocaleString()} - ${job.salaryMax.toLocaleString()}
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <Briefcase className="w-4 h-4" />
                <span className="text-sm font-medium">Type</span>
              </div>
              <p className="font-semibold text-gray-900 capitalize">{job.jobType}</p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <CalendarDays className="w-4 h-4" />
                <span className="text-sm font-medium">Posted</span>
              </div>
              <p className="font-semibold text-gray-900">
                {new Date(job.postedDate).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Match Breakdown */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-4">Match Breakdown</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-600 mb-1">Skills Match</p>
                <p className="text-2xl font-bold text-blue-600">
                  {job.capabilityMatch.breakdown.skillsMatch}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Experience</p>
                <p className="text-2xl font-bold text-blue-600">
                  {job.capabilityMatch.breakdown.experienceMatch}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Role Transition</p>
                <p className="text-2xl font-bold text-blue-600">
                  {job.capabilityMatch.breakdown.roleTransitionScore}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Cultural Fit</p>
                <p className="text-2xl font-bold text-blue-600">
                  {job.capabilityMatch.breakdown.culturalFitEstimate}%
                </p>
              </div>
            </div>
          </div>

          {/* Skills Alignment Radar */}
          <SkillsRadarChart
            skillsAlignment={job.skillsAlignment}
            height={350}
          />

          {/* Description */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">About This Role</h3>
            <p className="text-gray-700 leading-relaxed">{job.description}</p>
          </div>

          {/* Responsibilities */}
          {job.responsibilities.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Key Responsibilities</h3>
              <ul className="space-y-2">
                {job.responsibilities.map((resp, idx) => (
                  <li key={idx} className="flex gap-3 text-gray-700">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>{resp}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Requirements */}
          {job.requirements.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Requirements</h3>
              <div className="space-y-2">
                {job.requirements.map((req, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                    <span className={req.mandatory ? 'text-red-600 font-bold' : 'text-gray-400'}>
                      {req.mandatory ? '◆' : '◇'}
                    </span>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{req.skill}</p>
                      <p className="text-xs text-gray-600 capitalize">
                        {req.level} level {req.mandatory ? '(Required)' : '(Nice to have)'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Benefits */}
          {job.benefits.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Benefits</h3>
              <div className="grid grid-cols-2 gap-3">
                {job.benefits.map((benefit, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-gray-700">
                    <span className="text-green-600">✓</span>
                    <span>{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Match Reasoning */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">Why This Match?</h3>
            <ul className="space-y-2">
              {job.capabilityMatch.reasoning.map((reason, idx) => (
                <li key={idx} className="flex gap-2 text-gray-700 text-sm">
                  <span className="text-blue-600 font-bold">→</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition"
            >
              Close
            </button>
            <button
              onClick={onApply}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
            >
              Apply Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
