'use client';

import React, { useState, useMemo } from 'react';
import { Copy, Check } from 'lucide-react';
import clsx from 'clsx';

interface JDComparisonViewProps {
  originalJD: string;
  optimizedJD: string;
  loading?: boolean;
}

type ViewMode = 'full' | 'diff-only';

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged';
  content: string;
  lineNumber?: number;
}

export default function JDComparisonView({
  originalJD,
  optimizedJD,
  loading = false,
}: JDComparisonViewProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('full');
  const [copiedVersion, setCopiedVersion] = useState<'original' | 'optimized' | null>(null);

  // Simple diff algorithm - compares line by line
  const computeDiff = useMemo(() => {
    const originalLines = originalJD.split('\n');
    const optimizedLines = optimizedJD.split('\n');
    const diff: DiffLine[] = [];

    const maxLines = Math.max(originalLines.length, optimizedLines.length);

    for (let i = 0; i < maxLines; i++) {
      const origLine = originalLines[i] || '';
      const optLine = optimizedLines[i] || '';

      if (origLine === optLine) {
        if (viewMode === 'full') {
          diff.push({ type: 'unchanged', content: origLine, lineNumber: i + 1 });
        }
      } else {
        if (origLine) {
          diff.push({ type: 'removed', content: origLine, lineNumber: i + 1 });
        }
        if (optLine) {
          diff.push({ type: 'added', content: optLine, lineNumber: i + 1 });
        }
      }
    }

    return diff;
  }, [originalJD, optimizedJD, viewMode]);

  const handleCopy = (text: string, version: 'original' | 'optimized') => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedVersion(version);
      setTimeout(() => setCopiedVersion(null), 2000);
    });
  };

  const diffOnlyLines = computeDiff.filter((line) => line.type !== 'unchanged');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Before & After Comparison
        </h2>
        <p className="text-gray-600">
          Review the differences between your original and optimized job description
        </p>
      </div>

      {/* View Mode Toggle */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setViewMode('full')}
          className={clsx(
            'px-4 py-3 font-medium text-sm transition-colors border-b-2',
            viewMode === 'full'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          )}
        >
          Full Text
        </button>
        <button
          onClick={() => setViewMode('diff-only')}
          className={clsx(
            'px-4 py-3 font-medium text-sm transition-colors border-b-2',
            viewMode === 'diff-only'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          )}
        >
          Changes Only
          {diffOnlyLines.length > 0 && (
            <span className="ml-2 inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              {diffOnlyLines.length}
            </span>
          )}
        </button>
      </div>

      {/* Comparison Container */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Original JD */}
        <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
          {/* Header */}
          <div className="bg-gradient-to-r from-red-50 to-orange-50 border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Original</h3>
            <button
              onClick={() => handleCopy(originalJD, 'original')}
              disabled={loading}
              className={clsx(
                'flex items-center gap-2 px-3 py-1 rounded text-sm transition-colors',
                loading
                  ? 'opacity-50 cursor-not-allowed'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              )}
              title="Copy original text"
            >
              {copiedVersion === 'original' ? (
                <>
                  <Check className="w-4 h-4" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy
                </>
              )}
            </button>
          </div>

          {/* Content */}
          <div className="overflow-auto h-96">
            {viewMode === 'full' || computeDiff.filter((l) => l.type === 'removed').length === 0 ? (
              <pre className="p-6 text-sm text-gray-900 font-mono whitespace-pre-wrap break-words">
                {originalJD || <span className="text-gray-500">No content</span>}
              </pre>
            ) : (
              <div className="p-6">
                {computeDiff.map((line, index) => {
                  if (line.type === 'added') return null;
                  return (
                    <div
                      key={index}
                      className={clsx(
                        'py-1 px-3 mb-1 rounded text-sm font-mono',
                        line.type === 'removed'
                          ? 'bg-red-50 border-l-4 border-red-500 text-red-900'
                          : ''
                      )}
                    >
                      {line.content || <span className="text-gray-500">Empty line</span>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Optimized JD */}
        <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
          {/* Header */}
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Optimized</h3>
            <button
              onClick={() => handleCopy(optimizedJD, 'optimized')}
              disabled={loading}
              className={clsx(
                'flex items-center gap-2 px-3 py-1 rounded text-sm transition-colors',
                loading
                  ? 'opacity-50 cursor-not-allowed'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              )}
              title="Copy optimized text"
            >
              {copiedVersion === 'optimized' ? (
                <>
                  <Check className="w-4 h-4" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy
                </>
              )}
            </button>
          </div>

          {/* Content */}
          <div className="overflow-auto h-96">
            {viewMode === 'full' || computeDiff.filter((l) => l.type === 'added').length === 0 ? (
              <pre className="p-6 text-sm text-gray-900 font-mono whitespace-pre-wrap break-words">
                {optimizedJD || <span className="text-gray-500">No content</span>}
              </pre>
            ) : (
              <div className="p-6">
                {computeDiff.map((line, index) => {
                  if (line.type === 'removed') return null;
                  return (
                    <div
                      key={index}
                      className={clsx(
                        'py-1 px-3 mb-1 rounded text-sm font-mono',
                        line.type === 'added'
                          ? 'bg-green-50 border-l-4 border-green-500 text-green-900'
                          : ''
                      )}
                    >
                      {line.content || <span className="text-gray-500">Empty line</span>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <p className="text-sm font-semibold text-gray-600 mb-1">Original Length</p>
          <p className="text-2xl font-bold text-blue-600">
            {originalJD.length}
          </p>
          <p className="text-xs text-gray-600 mt-1">characters</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <p className="text-sm font-semibold text-gray-600 mb-1">Optimized Length</p>
          <p className="text-2xl font-bold text-green-600">
            {optimizedJD.length}
          </p>
          <p className="text-xs text-gray-600 mt-1">characters</p>
        </div>
        <div className={clsx(
          'rounded-lg p-4 text-center',
          optimizedJD.length > originalJD.length
            ? 'bg-yellow-50 border border-yellow-200'
            : 'bg-purple-50 border border-purple-200'
        )}>
          <p className="text-sm font-semibold text-gray-600 mb-1">Change</p>
          <p className={clsx(
            'text-2xl font-bold',
            optimizedJD.length > originalJD.length
              ? 'text-yellow-600'
              : 'text-purple-600'
          )}>
            {optimizedJD.length > originalJD.length ? '+' : ''}
            {optimizedJD.length - originalJD.length}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            ({Math.round((((optimizedJD.length - originalJD.length) / originalJD.length) * 100) * 10) / 10}%)
          </p>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">Legend</h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 bg-green-100 border-l-4 border-green-500 rounded" />
            <span className="text-sm text-gray-700">Added content</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 bg-red-100 border-l-4 border-red-500 rounded" />
            <span className="text-sm text-gray-700">Removed content</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 bg-gray-100 border-l-4 border-gray-300 rounded" />
            <span className="text-sm text-gray-700">Unchanged</span>
          </div>
        </div>
      </div>
    </div>
  );
}
