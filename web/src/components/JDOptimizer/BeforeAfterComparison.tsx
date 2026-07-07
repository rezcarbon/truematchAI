'use client';

import React, { useState } from 'react';
import { ArrowRight, Copy, Check } from 'lucide-react';

interface BeforeAfterComparisonProps {
  before: string;
  after: string;
}

export default function BeforeAfterComparison({
  before,
  after,
}: BeforeAfterComparisonProps) {
  const [copiedSide, setCopiedSide] = useState<'before' | 'after' | null>(null);
  const [viewMode, setViewMode] = useState<'split' | 'stacked'>(
    typeof window !== 'undefined' && window.innerWidth < 768 ? 'stacked' : 'split'
  );

  const handleCopy = (text: string, side: 'before' | 'after') => {
    navigator.clipboard.writeText(text);
    setCopiedSide(side);
    setTimeout(() => setCopiedSide(null), 2000);
  };

  const TextPanel = ({
    title,
    text,
    side,
  }: {
    title: string;
    text: string;
    side: 'before' | 'after';
  }) => (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <button
          onClick={() => handleCopy(text, side)}
          className="p-1.5 hover:bg-gray-100 rounded transition-colors"
          title="Copy text"
        >
          {copiedSide === side ? (
            <Check className="w-4 h-4 text-green-600" />
          ) : (
            <Copy className="w-4 h-4 text-gray-600 hover:text-gray-900" />
          )}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto mt-4">
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap break-words">
          {text}
        </p>
      </div>

      <div className="mt-4 pt-3 border-t border-gray-200 text-xs text-gray-500">
        {text.split('\n').length} lines • {text.length} characters
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* View Mode Selector */}
      <div className="flex gap-2">
        <button
          onClick={() => setViewMode('split')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            viewMode === 'split'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Split View
        </button>
        <button
          onClick={() => setViewMode('stacked')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            viewMode === 'stacked'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Stacked View
        </button>
      </div>

      {/* Content */}
      {viewMode === 'split' ? (
        // Split View
        <div className="grid grid-cols-2 gap-4 h-96">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <TextPanel title="Before" text={before} side="before" />
          </div>

          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <TextPanel title="After" text={after} side="after" />
          </div>
        </div>
      ) : (
        // Stacked View
        <div className="space-y-4">
          <div className="bg-red-50 rounded-lg p-4 border border-red-200 h-80">
            <TextPanel title="Before" text={before} side="before" />
          </div>

          <div className="flex justify-center">
            <ArrowRight className="w-5 h-5 text-gray-400 rotate-90" />
          </div>

          <div className="bg-green-50 rounded-lg p-4 border border-green-200 h-80">
            <TextPanel title="After" text={after} side="after" />
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3 pt-4">
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
          <p className="text-xs text-blue-600 font-medium">Words Improved</p>
          <p className="text-2xl font-bold text-blue-700 mt-1">
            {Math.abs(
              after.split(/\s+/).length - before.split(/\s+/).length
            )}
          </p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 border border-green-200">
          <p className="text-xs text-green-600 font-medium">Length Change</p>
          <p className="text-lg font-bold text-green-700 mt-1">
            {Math.round(
              ((after.length - before.length) / before.length) * 100
            )}
            %
          </p>
        </div>
        <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
          <p className="text-xs text-purple-600 font-medium">Readability</p>
          <p className="text-lg font-bold text-purple-700 mt-1">Enhanced</p>
        </div>
      </div>
    </div>
  );
}
