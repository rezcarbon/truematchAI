'use client';

import React, { useState } from 'react';
import { ChevronDown, Check, AlertCircle } from 'lucide-react';
import { OptimizationIssue } from '@/types/jd-optimizer';
import clsx from 'clsx';

interface IssueCardProps {
  issue: OptimizationIssue;
  isSelected?: boolean;
  onApplyFix?: () => void;
}

export default function IssueCard({
  issue,
  isSelected = false,
  onApplyFix,
}: IssueCardProps) {
  const [isExpanded, setIsExpanded] = useState(isSelected);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-50 border-red-200 text-red-700';
      case 'medium':
        return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      case 'low':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'clarity':
        return 'bg-purple-100 text-purple-800';
      case 'tone':
        return 'bg-pink-100 text-pink-800';
      case 'completeness':
        return 'bg-green-100 text-green-800';
      case 'structure':
        return 'bg-indigo-100 text-indigo-800';
      case 'engagement':
        return 'bg-amber-100 text-amber-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div
      className={clsx(
        'border rounded-lg transition-all',
        isExpanded
          ? 'bg-gray-50 border-gray-300'
          : getSeverityColor(issue.severity),
        issue.isFixed ? 'opacity-60' : ''
      )}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-start justify-between hover:bg-gray-100 transition-colors cursor-pointer group"
      >
        <div className="flex items-start gap-4 flex-1 text-left">
          {/* Status Icon */}
          <div className="mt-1">
            {issue.isFixed ? (
              <Check className="w-5 h-5 text-green-600" />
            ) : (
              <AlertCircle
                className={clsx(
                  'w-5 h-5',
                  issue.severity === 'high'
                    ? 'text-red-600'
                    : issue.severity === 'medium'
                      ? 'text-yellow-600'
                      : 'text-blue-600'
                )}
              />
            )}
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-gray-900">{issue.title}</h3>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(
                  issue.category
                )}`}
              >
                {issue.category}
              </span>
              <span className="text-xs font-medium text-gray-600 bg-gray-200 px-2 py-1 rounded">
                {issue.severity?.toUpperCase()}
              </span>
            </div>
            <p className="text-sm text-gray-700">{issue.description}</p>
          </div>
        </div>

        {/* Chevron */}
        <ChevronDown
          className={clsx(
            'w-5 h-5 text-gray-500 transition-transform flex-shrink-0 ml-4 mt-1',
            isExpanded ? 'rotate-180' : ''
          )}
        />
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 px-6 py-4 bg-white">
          <div className="space-y-4">
            {/* Problematic Text */}
            {issue.problematicText && (
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-2">
                  CURRENT TEXT
                </p>
                <div className="bg-red-50 border border-red-200 rounded px-3 py-2 text-sm text-gray-900 font-mono">
                  {issue.problematicText}
                </div>
              </div>
            )}

            {/* Suggestion */}
            {issue.suggestion && (
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-2">
                  SUGGESTED FIX
                </p>
                <div className="bg-green-50 border border-green-200 rounded px-3 py-2 text-sm text-gray-900 font-mono">
                  {issue.suggestion}
                </div>
              </div>
            )}

            {/* Explanation */}
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-2">
                WHY THIS MATTERS
              </p>
              <p className="text-sm text-gray-700">{issue.explanation}</p>
            </div>

            {/* Impact */}
            {issue.impact && (
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-2">
                  EXPECTED IMPACT
                </p>
                <p className="text-sm text-gray-700">{issue.impact}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-2 pt-4">
              {!issue.isFixed && (
                <button
                  onClick={onApplyFix}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors font-medium text-sm"
                >
                  Apply Fix
                </button>
              )}
              {issue.isFixed && (
                <div className="flex-1 px-4 py-2 bg-green-100 text-green-800 rounded text-center font-medium text-sm flex items-center justify-center gap-2">
                  <Check className="w-4 h-4" />
                  Fixed
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
