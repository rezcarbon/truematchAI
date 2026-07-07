'use client';

import React from 'react';

interface ProgressIndicatorProps {
  totalIssues: number;
  fixedIssues: number;
}

export default function ProgressIndicator({
  totalIssues,
  fixedIssues,
}: ProgressIndicatorProps) {
  const percentage =
    totalIssues === 0 ? 100 : Math.round((fixedIssues / totalIssues) * 100);

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            Issues Resolved
          </span>
          <span className="text-sm font-bold text-gray-900">
            {fixedIssues} of {totalIssues}
          </span>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-green-500 h-full transition-all duration-500 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>

        <p className="text-xs text-gray-500 mt-2">
          {percentage === 100
            ? 'All issues resolved!'
            : `${percentage}% complete`}
        </p>
      </div>

      {/* Step Indicators */}
      <div className="grid grid-cols-3 gap-2 mt-6">
        {Array.from({ length: 3 }).map((_, i) => {
          const step = i + 1;
          const isComplete =
            fixedIssues >= Math.ceil((totalIssues / 3) * step) ||
            totalIssues === 0;
          const isCurrent =
            !isComplete &&
            fixedIssues >= Math.ceil((totalIssues / 3) * (step - 1));

          return (
            <div
              key={step}
              className={`text-center py-2 px-3 rounded-lg transition-all ${
                isComplete
                  ? 'bg-green-100 border border-green-300'
                  : isCurrent
                    ? 'bg-blue-100 border border-blue-300'
                    : 'bg-gray-100 border border-gray-300'
              }`}
            >
              <p className="text-xs font-semibold text-gray-900">
                Phase {step}
              </p>
              <p
                className={`text-xs mt-1 ${
                  isComplete
                    ? 'text-green-700'
                    : isCurrent
                      ? 'text-blue-700'
                      : 'text-gray-600'
                }`}
              >
                {isComplete ? '✓ Done' : isCurrent ? 'In Progress' : 'Pending'}
              </p>
            </div>
          );
        })}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mt-6">
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-600">Total Issues</p>
          <p className="text-2xl font-bold text-gray-900">{totalIssues}</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 border border-green-200">
          <p className="text-xs text-green-700">Resolved</p>
          <p className="text-2xl font-bold text-green-600">{fixedIssues}</p>
        </div>
        <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
          <p className="text-xs text-orange-700">Remaining</p>
          <p className="text-2xl font-bold text-orange-600">
            {totalIssues - fixedIssues}
          </p>
        </div>
      </div>
    </div>
  );
}
